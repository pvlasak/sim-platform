FROM node:26-alpine AS build_step

RUN mkdir -p /home/app/src

COPY ./src /home/app/src
COPY ./package.json ./index.html ./vite.config.js /home/app

WORKDIR /home/app

RUN npm install

RUN npm run build

FROM nginx:alpine
COPY --from=build_step /home/app/dist /usr/share/nginx/html 
COPY nginx.conf /etc/nginx/conf.d/default.conf 
EXPOSE 80