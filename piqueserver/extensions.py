
import os
import importlib
import imp

from twisted.logger import Logger

log = Logger()


def check_scripts(script_names):
    '''Validation for a list of regular extension scripts.

    Check there are no duplicate scripts in the list of scripts names that is passed in.

    Args:
        script_names: The list of scripts names to be checked

    Return:
        bool: True if there are no duplicate scripts, False otherwise
    '''
    seen = set()
    dups = []
    for script in script_names:
        if script in seen:
            dups.append(script)
        else:
            seen.add(script)
    if dups:
        log.warn("Scripts included multiple times: {}".format(dups))
        return False
    return True


def check_game_mode(game_mode_name):
    '''Validation for a game mode script.

    Check if the game_mode is not a default one ('ctf' or 'tc').

    Args:
        game_mode_name: The game mode name to be checked

    Return:
        bool: True if the game mode is not a default one, False otherwise
    '''
    return game_mode_name not in ('ctf', 'tc')


def load_scripts(script_names, script_dir, script_type):
    '''Load script as module.

    Loads all scripts, matching the script_names, from the script_dir folder. The function also requires the
    specification of which type of scripts are passed in (e.g. "script", "gamemode", "testscript"). This is
    necessary for naming the namespace and error handling.

    Args:
        script_names: The list of script names to be loaded
        script_dir: The path to the corresponding scripts directory
        script_type: The script type ("script" for regular scripts and "gamemode" for game_mode script)

    Return:
        [module]: The list of module objects containing the loaded scripts
    '''
    script_objects = []

    for script in script_names[:]:
        try:
            # this finds and loads scripts directly from the script dir
            # no need for messing with sys.path
            f, filename, desc = imp.find_module(script, [script_dir])
            module = imp.load_module('piqueserver_{}_namespace_'.format(
                script_type) + script, f, filename, desc)
            script_objects.append(module)
        except ImportError as e:
            # warning: this also catches import errors from inside the script
            # module it tried to load
            try:
                module = importlib.import_module(script)
                script_objects.append(module)
            except ImportError as e:
                log.error(
                    "('{} {}' not found: {!r})".format(
                        script_type, script, e))
                script_names.remove(script)

    return script_objects


def load_scripts_regular_extension(script_names, script_dir):
    ''' Wrapper for load function

    It loads scripts in the case of regular extension scripts.

    Args:
        script_names: The list of script names to be loaded
        script_dir: The path to the corresponding scripts directory

    Return:
        [module]: The list of module objects containing the loaded scripts

    '''
    return load_scripts(script_names, script_dir, 'script')


def load_script_game_mode(script_name, script_dir):
    ''' Wrapper for load function

    It loads scripts in the case of game mode scripts. Prior to this, it checks if the game mode is not a
    default one (if it's a default no scripts should be loaded)

    Args:
        script_names: The list of script names to be loaded
        script_dir: The path to the corresponding scripts directory

    Return:
        [module]: The list of module objects containing the uploaded scripts

    '''
    if check_game_mode(script_name):
        return load_scripts(script_name, script_dir, 'gamemode')
    return []


def apply_scripts(scripts, config, protocol_class, connection_class):
    ''' Application of scripts modules

    It applies the script modules to the specified protocol and connection class instances, in order to build
    the resulting classes with all the additional features that the scripts implement (more information
    about how scripts are implemented and used can be found in the project documentation
    https://piqueserver.readthedocs.io/en/latest/architecture.html#extension-scripts).

    Args:
        scripts: List of scripts modules to apply
        config: It holds the dict of sections and options; this is required by the scripts
         logic
        protocol_class: The protocol class instance to update
        connection_class: The connection class instance to update

    Return:
        (FeatureProtocol, FeatureConnection): The updated protocol and connection class instances
    '''

    for script in scripts:
        protocol_class, connection_class = script.apply_script(
            protocol_class, connection_class, config.get_dict())

    return (protocol_class, connection_class)