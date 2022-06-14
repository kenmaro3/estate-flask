aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 486645269554.dkr.ecr.us-west-1.amazonaws.com
docker build -t estate-flask .
docker tag estate-flask:latest 486645269554.dkr.ecr.us-west-1.amazonaws.com/estate-flask:latest
docker push 486645269554.dkr.ecr.us-west-1.amazonaws.com/estate-flask:latest
