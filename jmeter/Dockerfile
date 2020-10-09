FROM radonconsortium/radon-ctt-agent:base

WORKDIR /opt

ENV PLUGIN_NAME jmeter
ENV PLUGIN_PATH "$PLUGIN_DIR/$PLUGIN_NAME"

RUN mkdir -p "$PLUGIN_PATH"

COPY . "$PLUGIN_PATH"

ENV JMETER_VERSION 5.2.1
ENV JMETER_NAME apache-jmeter-$JMETER_VERSION
ENV JMETER_BIN_URL http://ftp.halifax.rwth-aachen.de/apache/jmeter/binaries/$JMETER_NAME.zip
ENV JMETER_TMP_DL_PATH /tmp/jmeter.zip
ENV JMETER_LIB $PLUGIN_PATH/$JMETER_NAME/lib

ENV AWS_SDK_VERSION 1.11.878
ENV AWS_SDK_FILE_NAME aws-java-sdk-bundle-$AWS_SDK_VERSION.jar
ENV AWS_SDK_URL https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/$AWS_SDK_VERSION/$AWS_SDK_FILE_NAME

RUN apk add openjdk11-jre-headless

RUN wget -q $JMETER_BIN_URL -O $JMETER_TMP_DL_PATH &&\
    unzip -q $JMETER_TMP_DL_PATH -d $PLUGIN_PATH &&\
    rm $JMETER_TMP_DL_PATH

RUN wget -q $AWS_SDK_URL -O $JMETER_LIB/$AWS_SDK_FILE_NAME
ENV PATH="$PLUGIN_PATH/$JMETER_NAME/bin:$PATH"
