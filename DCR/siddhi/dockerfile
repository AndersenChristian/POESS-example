FROM siddhiio/siddhi-runner-alpine:latest

WORKDIR /apps
COPY OrderFoodAppDEMO.siddhi /apps/OrderFoodAppDEMO.siddhi

ENTRYPOINT ["sh", "-c", "/home/siddhi_user/siddhi-runner/wso2/runner/bin/carbon.sh -Dapps=/apps/OrderFoodAppDEMO.siddhi"]
