FROM nginx:1.11.1
COPY nginx.conf.template /etc/nginx/nginx.conf.template
CMD envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'
