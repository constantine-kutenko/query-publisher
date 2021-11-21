
build:
	@docker build \
		--tag query-publisher:0.0.1 \
		-f docker/Dockerfile .

run:
	@QUERY_LOG_FILE=/var/lib/proxysql/logs/queries.log \
		SLACK_WEBHOOK_URL=http://127.0.0.1:5000/ \
		INSTANCE_TYPE=mysql \
		LOG_LEVEL=debug \
		python3 src/app.py

docker:
	@docker run \
		--rm \
		--name query-publisher \
		--hostname query-publisher \
		-e ENVIRONMENT=development \
		-e QUERY_LOG_FILE=/var/log/proxysql/queries.log \
		-e SLACK_WEBHOOK_URL=http://slack:5000/ \
		-e INSTANCE_TYPE=mysql \
		-e LOG_LEVEL=debug \
		-v /var/lib/proxysql/logs/:/var/log/proxysql/ \
		-v ${PWD}/src/app.py:/app/app.py \
		-it query-publisher:0.0.1
