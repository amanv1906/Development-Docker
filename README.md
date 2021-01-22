# API
used for serving api on frontend.

1. Clone the repository

2. To build the image on local machine
```
sudo docker-compose build   (use sudo if non root user)
```
3. To run the image on container
```
docker-compose up
```
4. To stop the container

```
docker-compose down
```

1. Server will run on : **http://localhost:8000/**

   (you will see all the api there)

## Note 
1. When changes made in Dockerfile at that time you have to rebuild other wise all the changes will be reflected