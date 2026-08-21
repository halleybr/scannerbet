FROM nginx:alpine

# Remove config padrão
RUN rm /etc/nginx/conf.d/default.conf

# Copia nginx config
COPY nginx.conf /etc/nginx/conf.d/scannergreen.conf

# Copia o HTML
COPY index.html /usr/share/nginx/html/index.html

# Cache-busting headers no nível do build
LABEL maintainer="halleybr"

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -sf http://localhost/health || exit 1
