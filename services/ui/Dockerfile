FROM nginx:1.27-alpine

COPY services/ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY services/ui/index.html /usr/share/nginx/html/index.html

EXPOSE 80
