# -*- mode: python -*-

block_cipher = None

def Entrypoint(dist, group, name,
               scripts=None, pathex=None, hiddenimports=None,
               hookspath=None, excludes=None, runtime_hooks=None):
    import pkg_resources

    # get toplevel packages of distribution from metadata
    def get_toplevel(dist):
        distribution = pkg_resources.get_distribution(dist)
        if distribution.has_metadata('top_level.txt'):
            return list(distribution.get_metadata('top_level.txt').split())
        else:
            return []

    packages = hiddenimports or []
    for distribution in hiddenimports:
        packages += get_toplevel(distribution)

    scripts = scripts or []
    pathex = pathex or []
    # get the entry point
    ep = pkg_resources.get_entry_info(dist, group, name)
    print "entry_info %s" % ep.dist.location
    ep2 = pkg_resources.get_entry_info(dist, "easy_upgrade.actions", "github")
    ep3 = pkg_resources.get_entry_info(dist, "easy_upgrade.actions", "stow")
    print "Github location %s" % ep2.dist.location
    # insert path of the egg at the verify front of the search path
    pathex = [ep.dist.location] + pathex
    # script name must not be a valid module name to avoid name clashes on import
    script_path = os.path.join(WORKPATH, name + '-script.py')
    print "creating script for entry point", dist, group, name
    with open(script_path, 'w') as fh:
        fh.write("import {0}\n".format(ep.module_name))
        fh.write("import {0}\n".format(ep2.module_name))
        fh.write("import {0}\n".format(ep3.module_name))
        fh.write("{0}.{1}()\n".format(ep.module_name, '.'.join(ep.attrs)))
        for package in packages:
            fh.write("import {0}\n".format(package))

    return Analysis([script_path] + scripts, pathex, hiddenimports, hookspath, excludes, runtime_hooks)

a = Entrypoint('easy_upgrade', 'console_scripts', 'easy_upgrade',
             ['bin/easy_upgrade'],
             pathex=['/goinfre/tristan/src/github/easy_upgrade'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='easy_upgrade',
          debug=False,
          strip=None,
          upx=True,
          console=True )
