#!/bin/bash

# THIS SCRIPT REQUIRES BASH 4 OR HIGHER!!!

# This is a wrapper script for GooGios to be invoked by Nagios.
#
# The script adds an additional level of protection against mishaps.  In
# essence, the script tries to invoke GooGios, and - should GooGios crash,
# returns a pre-configured fall-back contact.
#
# The script can be invoked for example with
#
# As for the general idea behind GooGios, the existence of this layer of
# indirection is due to legacy and technical debt, not to good design.
#
# USAGE:
#   googios-wrapper.sh <roster> <contact-method> <message>
# Where:
#   <roster> is the file holding the configuration for a given roster
#   <contact-method> is either email or phone
#   <message> is the short message to be delivered as alarm


# =============================================================================
# MODIFY THIS PART OF THE SCRIPT TO MEET YOUR NEEDS!
# =============================================================================

declare -A FALLBACKS=(
    ["email"]="foo@bar.baz"
    ["phone"]="05551234")
declare -A COMMANDS=(
    ["email"]='mailx -s "$MESSAGE" $CONTACT < /dev/null'
    ["phone"]='mailx -s "$MESSAGE" $CONTACT@my.sms.gateway.com < /dev/null')

# =============================================================================

# validate and parse arguments
if  ! [[ $1 && $2 && $3 ]] || ! [[ $2 == 'email' || $2 == 'phone' ]]
then
    echo "USAGE: googios-wrapper.sh <roster> <contact-method> <message>"
    exit 1
fi

ROSTER=$1
METHOD=$2
MESSAGE=$3

# retrieve contact information for on-call person
CONTACT=`googios $ROSTER current $METHOD`
if [ ! $? == 0 ]
then
    CONTACT="${FALLBACKS[$METHOD]}"
fi

# alarm propagation
eval "${COMMANDS[$METHOD]}"
