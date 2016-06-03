#!/bin/bash

function _os()
{
  local o="$1"
  if [ -z "$1" -o "$1" == "auto" ]; then
   o=`uname`
  fi
  
  case "$o" in

    [lL]in | [lL]inux)
      echo "lin"
      ;;

    [mM]ac | Darwin)
      echo "mac"
      ;;

    [wW]in | [wW]indows)
      echo "win"
      ;;

    [aA]ndroid)
      echo "android"
      ;;

    i[Oo][Ss])
      echo "ios"
      ;;

    MINGW*_*)
      echo "win"
      ;;
      
    Cygwin|CYGWIN_*)
      echo "win"
      ;;

    *)
      echo "${BASH_SOURCE[0]}, line $LINENO: error: unrecognized operating system \"$o\"" >&2
      exit 1
      ;;

  esac
}

function _arch()
{
  local o=$1
  local m=$2

  if [ -z "$m" -o "$m" == "default" ]; then

    case "$o" in
      win)
        if [ ! -z "$PROCESSOR_ARCHITEW6432" ]; then
          m="$PROCESSOR_ARCHITEW6432"
        else
          m="$PROCESSOR_ARCHITECTURE"
        fi
        ;;

      lin)
        m=`uname -m`
        ;;

      mac)
        m="x86+x64"
        ;;

      android)
        m="armv7"
        ;;

      ios)
        m="x86+armv7+arm64"
        ;;

      *)
        echo "${BASH_SOURCE[0]}, line $LINENO: error: unrecognized operating system \"$o\"" >&2
        exit 1
        ;;
    esac

  fi

  case "$m" in

    x86|x64|armv5|armv6|armv7|arm64|x86+x64|armv6+armv7|x86+armv7+arm64)
      echo "$m"
      ;;

    i*86)
      echo "x86"
      ;;

    x86_64|AMD64|IA64)
      echo "x64"
      ;;

    arm5|armeabi)
      echo "armv5"
      ;;

    arm6)
      echo "armv6"
      ;;

    arm|arm7|armeabi-v7a)
      echo "armv7"
      ;;

    *)
      echo "${BASH_SOURCE[0]}, line $LINENO: error: unrecognized architecture \"$m\"" >&2
      exit 1
      ;;

  esac
}

function _platformdir()
{
  local o=$1
  local m=$2

  case "$o-$m" in

    lin-x86|lin-x64)
      echo "$o-$m"
      ;;

    win-x86|win-x64)
      echo "$o-$m"
      ;;

    mac-x86|mac-x64|mac-x86+x64)
      echo "$o-$m"
      ;;

    ios-x86|ios-armv7+arm64|ios-x86+armv7+arm64)
      echo "$o-$m"
      ;;

    android-x86)
      echo "$o-$m"
      ;;

    android-armv5)
      echo "$o-armeabi"
      ;;

    android-armv7)
      echo "$o-armeabi-v7a"
      ;;

    *)
      echo "${BASH_SOURCE[0]}, line $LINENO: error: unsupported operating-system/architecture combination: \"$o-$m\"" >&2
      exit 1
      ;;
  esac
}

function _exe_suffix()
{
  case "$1" in

    win)
      echo ".exe"
      ;;

  esac
}

function _have_shared_libs()
{
  test "$1" != "ios"
}

function _lib_prefix()
{
  case "$1" in

    lin | mac | android)
      echo "lib"
      ;;

  esac
}

function _lib_suffix()
{
  case "$1" in

    lin | android)
      echo ".so"
      ;;

    mac)
      echo ".dylib"
      ;;

    win)
      echo ".dll"
      ;;

  esac
}

_OS=`_os auto`
_ARCH=`_arch $_OS default`
_PLATFORMDIR=`_platformdir $_OS $_ARCH`
_EXE_SUFFIX=`_exe_suffix $_OS`
_LIB_PREFIX=`_lib_prefix $_OS`
_LIB_SUFFIX=`_lib_suffix $_OS`

if [ "$_OS" == "win" ]; then
  case `uname` in
    MINGW32_*)
      _WPOSIX="MinGW"
      ;;
    Cygwin|CYGWIN_*)
      _WPOSIX="Cygwin"
      ;;
  esac
fi
