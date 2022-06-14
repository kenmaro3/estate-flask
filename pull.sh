aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 486645269554.dkr.ecr.us-west-1.amazonaws.com
docker pull 486645269554.dkr.ecr.us-west-1.amazonaws.com/estate-flask:latest
docker tag 486645269554.dkr.ecr.us-west-1.amazonaws.com/estate-flask:latest estate-flask:latest
