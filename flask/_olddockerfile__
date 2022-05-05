# Step 1: Import the Os
FROM devashishupadhyay/scikit-learn-docker

# Step 2: Install pip and Python Dependencies
# RUN apt-get add cmd:pip3 --no-cache python3-dev \
#     && pip3 install --upgrade pip

# Step 3: Create a Work Directory
WORKDIR /app

# Step 4: copy all Project Files
COPY . /app

# Step 5: Install all Dependencies for WSGI
# RUN set -e; \
# 	apt-get add --no-cache --virtual .build-deps \
# 		gcc \
#         g++\
# 		libc-dev \
# 		linux-headers \
# 	; \
# 	pip3 --no-cache-dir install -r requirements.txt; \
# 	apt-get del .build-deps;
# RUN apk update && apk add gcc
# # RUN apk update && apk add build-essential
# RUN apk add --no-cache gcc python3-dev
# RUN apk add --no-cache gcc libc-dev linux-headers

RUN pip3 install --no-cache-dir -r requirements.txt
# Step 6:  run the command to start uWSGI
CMD ["uwsgi", "app.ini"]