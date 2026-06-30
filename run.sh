# Image used does not allow shebang execution

# system architecture
ARCH=$(uname -m)
OS=$(uname -s)
echo "=== System Info ==="
echo -e "Architecture: $ARCH"
echo -e "Operating System: $OS\n"

# exit on error, unset vars, pipe failures
set -euo pipefail

# usage instructions for the script
show_help() {
    cat << EOF
Usage: ./run.sh [OPTIONS] [ARGS...]

OPTIONS:
    --help              Show this help message and exit
    --run               Start the application engine
EOF
}

# default action when no arguments are given
if [ $# -eq 0 ]; then
    echo "Error: At least one argument is required."
    show_help
    exit 1
fi

# parse command line arguments
case $1 in
    --help)
        show_help
        exit 0
    ;;

    --run)
        echo "Starting the application engine..."
        shift 1
        python src/main.py "$@"
    ;;

    *)
        echo "Unknown option: $1"
        show_help
        exit 1
    ;;
esac