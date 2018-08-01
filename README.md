EPICS sources
=============
All in one. For EPICS base and modules

Build: Check system enviroment first ( `source epics_example.sh` ). Then `make -f Makefile.all`, will install into `/opt/epics/` and `/opt/epics/modules`

You can put `epics-linux-x86_64.conf` under `/etc/ld.so.conf.d/` if you use linux-x86\_64 ( other system can modify from it )

~~Setup development environment: `./setupRemote.sh`~~

NOTE: If you use `make -jX` failed, try to build `extensions` first. ( `devIocStats` in `modules` depends on `msi` in `extensions` )

Env variable
------------
Three most important for building and installation:

**EPICS_HOST_ARCH** must setup, because [bug](https://bugs.launchpad.net/epics-base/+bug/1719670) in EPICS building system(They did not copy starup scripts with contain EpicsHostArch)

**BASE_PATH** for epics base (install to and search) location

**BASE\_SUPPORT\_PATH** for epics modules

For details see `epics_example.sh`, users would create `epics.sh` based on it. You can source it ( before building ), copy them in zshrc/bashrc, or put it under `/etc/profile.d`(for bash).

Ways to add a new package
-------------------------
For [epics modules](http://aps.anl.gov/epics/modules/index.php) (github repo: https://github.com/epics-modules ), it is recommended to put the module under directory **modules/**.

For [epics extensions](http://www.aps.anl.gov/epics/extensions/index.php) ( github repo: https://github.com/epics-extensions), put it under directory **extensions/src/** if its doc said that.

Some strategies to add/import new packages:

* Fetch sources and put it into master branch directly. NOT RECOMMENDED.
* Use [git submodule](https://git-scm.com/docs/git-submodule). It is a good idea for optional packages, and is easy to push to upstream.
* Use [git subtree](http://git.kernel.org/cgit/git/git.git/plain/contrib/subtree/git-subtree.txt). Introduction: https://blogs.atlassian.com/2013/05/alternatives-to-git-submodule-git-subtree/. It will copy files into current repo. It is good for necessary packages. But you should care about the commit history.
* Use [subtree merge strategy](https://git-scm.com/book/en/Git-Tools-Subtree-Merging). It is similar to `git subtree`, but low level and complicated. I use this method. Some tutorial: https://help.github.com/articles/about-git-subtree-merges/ and https://www.kernel.org/pub/software/scm/git/docs/howto/using-merge-subtree.html.
* Other tools like [git-subrepo](https://github.com/ingydotnet/git-subrepo). `git subrepo` may be easier to squash and update dependencies. Just `git subrepo clone <remote_repo> <sub_dir>` to add new packages

Tip: `git subtree` command and "subtree merge strategy" are different. The former is easier to use.

After importing new packages. You need to modify some files such as README.md, Makefile, etc to make everything work. 

**NOTE** After checking EPICS build system, it is better to configure `CONFIG_SITE.local`, `CONFIG_SITE.$(EPICS_HOST_ARCH).**` than modifying `CONFIG_SITE`.

### Example of subtree merge strategy ###

This is how I add new packag (use `asynDriver` module as an example).

1. Fetch upstream sources. (e.g. `git add asyn https://github.com/epics-modules/asyn.git && git fetch asyn`)
2. Checkout a new branch. (e.g. `git checkout -b asyn asyn/master`)
3. `git checkout master`
4. Use [git read-tree](https://git-scm.com/docs/git-read-tree). (e.g. `git read-tree -u --prefix=modules/asyn asyn`)
5. Commit. (e.g. `git commit -m "subtree merge 'asyn' to dir 'modules/asyn'`)
6. Make compilation work. I need to modify **RELEASE**(to check dependency), **CONFIG\_SITE.\*\***(to set install location) or other files.
7. Check/update `README.md`, `setupRemote.sh`, `modules/Makefile`, `modules/configure/EPICS_BASE`, etc.

Do not forget to push.

### Ways to merge sub-directory's change into their own branch (contribute back to upstream) ###

Maybe we could have better ways to solve this. Here is what I will do when I want to merge master's commits back to sub repo.

1. Find commits about this sub-directory. (`git filter-branch subdirectory-filter <sub-dir-name>`)
2. Checkout this sub branch. (`git checkout <sub-dir-corresponding-branch>`) 
3. Apply commits. (`git cherry-pick <commits>`)
4. Push. (`git push <sub-remote> HEAD:<sub-upstream-branch>`)
5. Change back and reset. (`git checkout master` && `git reset HEAD@{4}`(may not 4)

If we do not use filter-branch, then git reset should not be used.

### Update local subtree with remote upstream (tracking sub projects' corresponding upstream) ###
We can merge from the upstream's branch and pick its commit into our sub-dir under master branch. We can consider about a few of commands (with or without commits)

* `git diff`, `git diff-tree` to generate patch then `git apply`
* `git read-tree`, use a new dir then move back (or just delete sub dir first)
* `git pull` with subtree merge strategy:

`git pull -s recursive -X theirs -Xsubtree=base --squash --no-commit --no-log --allow-unrelated-histories <remote_host> <remote_sub_branch>`

or:

`cd <sub_dir> && git pull -s subtree <remote_sub_branch> master`

Dependency
----------
system libs: readline, perl, re2c, rpcsvc-proto, libtirpc

asyn: ipac seq

busy: asyn

calc: sscan seq

logioc: (system libs) libcurl

sscan: seq

stream(StreamDevice): asyn calc

modbus: asyn

caPutLog: logioc

medm: (system libs) libx11 libxt libxmu motif(eg: openmotif, lesstif)

For Archlinux ( pacman based ) user, you can run:

`pacman -S readline perl re2c openmotif libx11 libxt libxmu curl libtirpc --needed --noconfirm`

(After installing perl, please restart system first to make perl's environment variable work, then build epics)

NOTE, we use base-3.14.12.6-pre1, asyn-4.28

Problems and Solution
---------------------
* medm fonts alias ( see http://www.aps.anl.gov/epics/extensions/medm/index.php ), medmfonts.ali.txt is already in our dir. For Archlinux, put alias into `/usr/share/fonts/misc/fonts.alias`.
* medm compilation failed. `libXm.a`/`libXt.a` or something may failed to find (E.g. on Debian/Ubuntu) (Compilation ok on Archlinux, Gentoo)
(1) According to [EPICS AppDevGuide](http://www.aps.anl.gov/epics/base/R3-14/12-docs/AppDevGuide.pdf), there are some env flags to control compilation, use `PROD_LIBS_XXX`, `XXXX_SYS_LIBS` instead of `USR_LIBS_XXX` flags may be helpful (ask make to use shared instread of static libs);   
(2) Or just get libXm.a,libXt.a (static libs) and put it into right directory that Makefile searched for (after reading error output carefully);  
(3) Modify `MOTIF_LIB`, `X11_LIB` in `extensions/configure/os/CONFIG_SITE.linux-x86_64.linux-x86_64`;  
(4) On Debian 9, There is only i386 libxp, you can follow instruction in `medm/medm/Makefile`: just comment out Xp
* SUPPORT modules path conflicting in RELEASE. Check installed modules RELEASE or reinstall them.

TODO / Known Problems
---------------------
use EPICS build system for sources' root dir and modules dir ( Then we can make clean, make distclean, make rebuild, etc )

support install into current dir ( workaround: `export BASE_SUPPORT_PATH=$PWD` )

support devIocStats ( now have a workaround, hacked its configuration. Another problem: devIocStats depend on extensions msi, this means make -jX would fail )

support our iocs

setup files for medm/caQtDM ( *.ui *.adl )

check system platform ( some of packages can be built for windows )

consider about version control
