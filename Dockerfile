# Dockerfile for Wallabag on Google Cloud Run with PostgreSQL support
# Using PHP 8.1+ and local Wallabag source code

# Build arguments
ARG PHP_VERSION=8.1
ARG WALLABAG_VERSION=2.5.2
ARG COMPOSER_VERSION=2

# ===== Builder Stage =====
FROM composer:${COMPOSER_VERSION} AS composer

# ===== Final Image =====
FROM php:${PHP_VERSION}-apache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libicu-dev \
    libpq-dev \
    libzip-dev \
    zlib1g-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libwebp-dev \
    libxml2-dev \
    libonig-dev \
    libtidy-dev \
    git \
    unzip \
    curl \
    cron \
    sudo \
    wait-for-it \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure and install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j$(nproc) \
        intl \
        pdo \
        pdo_pgsql \
        pgsql \
        zip \
        gd \
        opcache \
        calendar \
        bcmath \
        dom \
        mbstring \
        xml \
        tidy \
        sockets

# Copy composer from builder stage
COPY --from=composer /usr/bin/composer /usr/bin/composer

# Enable Apache modules
RUN a2enmod rewrite headers ssl

# Set Apache document root
ENV APACHE_DOCUMENT_ROOT=/var/www/html/web
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/!${APACHE_DOCUMENT_ROOT}/!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Configure Apache security headers
RUN { \
    echo '<IfModule mod_headers.c>'; \
    echo '    Header set X-Content-Type-Options "nosniff"'; \
    echo '    Header set X-XSS-Protection "1; mode=block"'; \
    echo '    Header set X-Frame-Options "SAMEORIGIN"'; \
    echo '    Header set Referrer-Policy "strict-origin-when-cross-origin"'; \
    echo '    Header set Content-Security-Policy "default-src \'self\'; script-src \'self\' \'unsafe-inline\' \'unsafe-eval\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; connect-src \'self\'; font-src \'self\'; object-src \'none\'; media-src \'self\'; frame-src \'self\'; base-uri \'self\'; form-action \'self\';"'; \
    echo '</IfModule>'; \
} > /etc/apache2/conf-available/security-headers.conf \
&& a2enconf security-headers

# Set working directory
WORKDIR /var/www/html

# Copy local Wallabag source code
COPY ./backend/src/wallabag-source/ /var/www/html/

# Copy parameters template
COPY ./backend/src/config/parameters.yml.template /var/www/html/app/config/parameters.yml.template

# Set up proper directory permissions
RUN mkdir -p /var/www/html/var/cache /var/www/html/var/logs /var/www/html/var/sessions \
    && chown -R www-data:www-data /var/www/html/var \
    && chmod -R 775 /var/www/html/var

# Install Composer dependencies
RUN COMPOSER_ALLOW_SUPERUSER=1 composer install --no-dev --optimize-autoloader --ignore-platform-req=composer --no-scripts

# Configure PHP
RUN echo "memory_limit = 512M" > /usr/local/etc/php/conf.d/wallabag-memory.ini \
    && echo "max_execution_time = 90" > /usr/local/etc/php/conf.d/wallabag-timeout.ini \
    && echo "upload_max_filesize = 10M" > /usr/local/etc/php/conf.d/wallabag-upload.ini \
    && echo "post_max_size = 10M" > /usr/local/etc/php/conf.d/wallabag-post.ini \
    && echo "date.timezone = UTC" > /usr/local/etc/php/conf.d/wallabag-timezone.ini \
    && echo "opcache.memory_consumption = 128" > /usr/local/etc/php/conf.d/wallabag-opcache.ini \
    && echo "opcache.interned_strings_buffer = 8" >> /usr/local/etc/php/conf.d/wallabag-opcache.ini \
    && echo "opcache.max_accelerated_files = 4000" >> /usr/local/etc/php/conf.d/wallabag-opcache.ini \
    && echo "opcache.revalidate_freq = 60" >> /usr/local/etc/php/conf.d/wallabag-opcache.ini \
    && echo "opcache.fast_shutdown = 1" >> /usr/local/etc/php/conf.d/wallabag-opcache.ini

# Copy entrypoint script
COPY ./backend/src/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy healthcheck script
COPY ./backend/src/docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Configure cron jobs for background tasks
COPY ./backend/src/docker/crontab /etc/cron.d/wallabag
RUN chmod 0644 /etc/cron.d/wallabag

# Create directories for API keys
RUN mkdir -p /var/www/html/data/keys \
    && chown -R www-data:www-data /var/www/html/data \
    && chmod -R 750 /var/www/html/data

# Expose port
EXPOSE 80

# Set environment variables
ENV WALLABAG_DOMAIN=localhost \
    SYMFONY_ENV=prod \
    SYMFONY_DEBUG=0 \
    WALLABAG_DATABASE_DRIVER=pdo_pgsql

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD /healthcheck.sh

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]