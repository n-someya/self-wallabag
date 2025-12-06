#!/bin/bash
set -eo pipefail

# This script is for debugging the Wallabag Docker container

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Wallabag Debug Tool ===${NC}"

# Check if the container is running
if ! docker ps | grep -q 'self-wallabag'; then
    echo -e "${RED}Error: Wallabag container is not running!${NC}"
    echo -e "${YELLOW}Use ./run-wallabag.sh to start the container first.${NC}"
    exit 1
fi

# Get container ID
CONTAINER_ID=$(docker ps -qf "name=self-wallabag")

echo -e "${GREEN}=== Container Information ===${NC}"
docker inspect $CONTAINER_ID | grep -E 'Name|Image|Status|Health'

echo -e "${GREEN}=== Environment Variables ===${NC}"
docker exec $CONTAINER_ID env | grep -E 'WALLABAG|SYMFONY'

echo -e "${GREEN}=== Container Logs (last 50 lines) ===${NC}"
docker logs --tail 50 $CONTAINER_ID

echo -e "${GREEN}=== Database Connection Test ===${NC}"
docker exec $CONTAINER_ID bash -c '
source /entrypoint.sh > /dev/null 2>&1
DATABASE_HOST=${WALLABAG_DATABASE_HOST:-postgres}
DATABASE_PORT=${WALLABAG_DATABASE_PORT:-5432}
DATABASE_NAME=${WALLABAG_DATABASE_NAME:-postgres}
DATABASE_USER=${WALLABAG_DATABASE_USER:-postgres}
DATABASE_PASSWORD=${WALLABAG_DATABASE_PASSWORD:-postgres}
DATABASE_SSL_MODE=${WALLABAG_DATABASE_SSL_MODE:-require}

PGPASSWORD=$DATABASE_PASSWORD pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER
if [ $? -eq 0 ]; then
    echo "Database connection successful"
else
    echo "Failed to connect to database"
fi
'

echo -e "${GREEN}=== Filesystem Status ===${NC}"
docker exec $CONTAINER_ID bash -c '
echo "Checking important directories:"
echo "- Data directory:"
ls -la /var/www/html/data/
echo "- Var directory:"
ls -la /var/www/html/var/
echo "- Checking permissions:"
find /var/www/html/var -type d -not -perm 775 2>/dev/null || echo "All directories have correct permissions"
'

echo -e "${GREEN}=== PHP Configuration ===${NC}"
docker exec $CONTAINER_ID bash -c 'php -i | grep -E "memory_limit|max_execution_time|upload_max_filesize|post_max_size|date.timezone"'

echo -e "${GREEN}=== Available Services ===${NC}"
docker exec $CONTAINER_ID bash -c 'ps aux | grep -E "(apache|cron|php)"'

echo -e "${GREEN}=== API Key Information ===${NC}"
docker exec $CONTAINER_ID bash -c '
if [ -f /var/www/html/data/keys/api-key.txt ]; then
    echo "API Key is configured:"
    cat /var/www/html/data/keys/api-key.txt
else
    echo "No API Key found"
fi
'

echo -e "${GREEN}=== Testing Web Access ===${NC}"
curl -I http://localhost:8080 || echo -e "${RED}Failed to access the web interface${NC}"

echo -e "${BLUE}=== Debug Complete ===${NC}"
echo -e "${YELLOW}If you're still experiencing issues, try these commands:${NC}"
echo -e "- ${GREEN}docker exec -it self-wallabag bash${NC} (to get a shell inside the container)"
echo -e "- ${GREEN}docker-compose down && docker-compose up -d${NC} (to restart the services)"

exit 0