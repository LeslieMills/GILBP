FROM nginx:latest

# Remove the default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Replace with our own nginx.conf
COPY nginx.conf /etc/nginx/conf.d/

#Perform upgrade (L.M)
RUN apt update -y && apt full-upgrade -y && apt autoremove -y && apt clean -y && apt autoclean -y
RUN apt-get install apt-utils -y
