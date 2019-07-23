#!/usr/bin/env python3
# Fuck shell/bash so I use python

"""
Script to configure epics modules automatically.
Generate CONFIG_SITE.* EPICS_BASE.* SUPPORT* files
"""

from collections import namedtuple
from pathlib import Path
import os
import argparse

ClassConfig = namedtuple('ClassConfig', 'fname content')

class EpicsConfig:
    _CONFIGS = []
    @staticmethod
    def __init__(fname, content, module=''):
        filedir = os.path.dirname(os.path.abspath(__file__))
        realfname = os.path.join(filedir, module, "configure", fname)
        EpicsConfig._CONFIGS.append(ClassConfig(realfname, content))
    @staticmethod
    def dump(envs, write=False):
        for c in EpicsConfig._CONFIGS:
            outfile = c.fname.format_map(envs)
            outcontent = c.content.format_map(envs)
            print('----------------')
            print('fname:', outfile)
            if write:
                with Path(outfile).open('w') as f:
                    f.write(outcontent)
            else:
                print('content:', outcontent) 


epics_env_config_defaults = {
    'BASE_PATH': "/opt/epics",
    'BASE_SUPPORT_PATH': "/opt/epics/modules",
    'EPICS_HOST_ARCH': 'linux-x86_64',
}

_alias = {
    'EPICS_BASE': 'BASE_PATH',
    'SUPPORT': 'BASE_SUPPORT_PATH',
}

_depends = {
    # value must be iterable
    'asyn': ['ipac', 'seq',],
    'busy': ['asyn', 'autosave',],
    'sscan': ['seq',],
    'calc': ['sscan',],
    'devIocStats': ['seq',],
    'alive': [],
    # If a package does not have depedency, just with empty list
}

module_alias = {
    # module dir name: module support name
    'seq': 'SNCSEQ',
}

support_fname = "SUPPORT.{EPICS_HOST_ARCH}"
support_content = """
-include $(TOP)/../configure/SUPPORT.local
SUPPORT=${{BASE_SUPPORT}}
-include $(TOP)/configure/SUPPORT.local
"""
EpicsConfig(support_fname, support_content)

base_fname = "EPICS_BASE.{EPICS_HOST_ARCH}"
base_content = """
-include $(TOP)/../configure/EPICS_BASE.local
EPICS_BASE=${{BASE_PATH}}
SUPPORT=${{BASE_SUPPORT_PATH}}
-include $(TOP)/configure/EPICS_BASE.local
"""
EpicsConfig(base_fname, base_content)

root_config_site = "CONFIG_SITE.local"
root_config_content = """
INSTALL_LOCATION={SUPPORT}
"""
EpicsConfig(root_config_site, root_config_content)

config_site_fname = "CONFIG_SITE.{EPICS_HOST_ARCH}.Common"
# `support` will be formatted later
config_site_content = """
-include $(TOP)/../configure/CONFIG_SITE.local
INSTALL_LOCATION={{SUPPORT}}/{module}
-include $(TOP)/configure/CONFIG_SITE.local
"""
# would render config site in main module func

release_fname = "RELEASE.{EPICS_HOST_ARCH}.Common"
release_content = """
-include $(TOP)/../configure/RELEASE.local
-include $(TOP)/configure/RELEASE.local
"""
# would append default SUPPORT to release later

def GenerateDepends(depends: dict, modules: set, write=False):
    """Generate modules to be compiled and their depedencies
    Makefile will try to include the outputfile Makefile.depedency
    :foramt: ```
        DIR += <module1>
        DIR += <module2>
        <module1>_DEPEND_DIRS += <module2>
    ```
    """
    template = """DIRS += {module}
    """
    output = ""
    for module in modules:
        output = f"""{output}
        {template.format(module=module)}
        """
    for k, v in depends.items():
        if len(v) == 0:
            continue
        output = f"""{output}
        {k}_DEPEND_DIRS += {" ".join(v)}
        """
    if write:
        filedir = os.path.dirname(os.path.abspath(__file__))
        outfile = Path(filedir).joinpath('Makefile.dependency')
        with outfile.open(mode='w') as f:
            f.write(output)
        print("check file", outfile)
    else:
        print("depedency:\n", output)

def GenerateReleaseSupport(modules):
    """ Generate other modules path for this module
    :format: ```
        <module1_alias>={SUPPORT}/<module1>
    ```
    And {SUPPORT} will be will be rendered later
    """
    template = """
    """
    for m in modules:
        name = m.upper()
        if m in module_alias:
            name = module_alias[m].upper()
        template += f"""{name}={{SUPPORT}}/{m}
        """
#        template += name + """={SUPPORT}/""" + f"""{m}
    return template

# XXX must be executed under epics-modules root dir
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', help='do not write config files', action='store_true', default=False)
    args = parser.parse_args()
    print(args)

    from os import getenv
    # These variable could be overrided by local script
    epics_env_config = {
        k: getenv(k) or v for k, v in epics_env_config_defaults.items()
    }
    epics_env_config.update({
        a: epics_env_config[n] for a, n in _alias.items()
    })
    depends: dict = _depends
    # NOTE not tested yet
    try:
        from config_site_local import *
    except ImportError as e:
        pass
    modules = set()
    for k, v in depends.items():
        modules.add(k)
        [ modules.add(vv) for vv in v ]
    print("epics_env_config:", epics_env_config)
    print("depends:", depends)
    print("modules:", modules)

    
    # Configure depedency for modules
    for m in modules:
        # TODO move this support gen to root configure
        supports = GenerateReleaseSupport(modules)
        EpicsConfig(
            release_fname,
            supports + release_content,
            module=m)
#    list(map(lambda m:
        EpicsConfig(
            config_site_fname, 
            config_site_content.format(module=m),
            module=m)
#        , modules
#    ))


    if args.dry_run:
        EpicsConfig.dump(epics_env_config)
        GenerateDepends(depends, modules)
    else:
        EpicsConfig.dump(epics_env_config, write=True)
        GenerateDepends(depends, modules, write=True)


