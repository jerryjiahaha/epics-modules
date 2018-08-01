/*************************************************************************\
* Copyright (c) 2009 Helmholtz-Zentrum Berlin fuer Materialien und Energie.
* Copyright (c) 2002 The University of Chicago, as Operator of Argonne
*     National Laboratory.
* Copyright (c) 2002 The Regents of the University of California, as
*     Operator of Los Alamos National Laboratory.
* EPICS BASE Versions 3.13.7
* and higher are distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution.
\*************************************************************************/

/* osdPwdInfo.c - PWD info strings: posix implementation = getpwd() */

/*
 *  Author: Ralph Lange (HZB/BESSY)
 *
 *  Modification History
 *  2009-05-20 Ralph Lange (HZB/BESSY)
 *     Restructured OSD parts
 *
 */

#include <devIocStats.h>

#define MAX_CWD_SIZE  1024

static char *notavail = "<not available>";
static char pwd[MAX_CWD_SIZE] = "";

int devIocStatsInitPwdInfo (void) { return 0; }

int devIocStatsGetPwd (char **pval)
{
    if (!getcwd(pwd, MAX_CWD_SIZE)) {
        *pval = notavail;
        return -1;
    } else {
        *pval = pwd;
        return 0;
    }
}
