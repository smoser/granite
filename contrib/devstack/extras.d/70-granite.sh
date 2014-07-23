# granite.sh - Devstack extras script to install native lxc

if [[ $VIRT_DRIVER == "granite" ]]; then
	if [[ $1 == "source" ]]; then
       # Keep track of the current directory
       SCRIPT_DIR=$(cd $(dirname "$0") && pwd)
       TOP_DIR=$SCRIPT_DIR

       echo $SCRIPT_DIR $TOP_DIR

       # Import common functions
       source $TOP_DIR/functions

       # Load local configuration
       source $TOP_DIR/stackrc

       FILES=$TOP_DIR/files

       # Get our defaults
       source $TOP_DIR/lib/nova_plugins/hypervisor-granite
	   source $TOP_DIR/lib/granite
	   elif [[ $2 == "install" ]] ; then
		  echo_summary "Configuring granite"
		  if is_ubuntu; then
		  	  install_package --force-yes lxc lxc-dev

		  fi
		  install_granite
	fi
fi
