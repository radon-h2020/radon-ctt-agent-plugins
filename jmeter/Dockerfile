FROM radonconsortium/radon-ctt-agent:base

WORKDIR /opt

ENV PLUGIN_NAME jmeter
ENV PLUGIN_PATH /opt/$CTT_AGENT_NAME/plugins/$PLUGIN_NAME
RUN mkdir -p $PLUGIN_PATH
COPY . $PLUGIN_PATH

ENV JMETER_VERSION 5.2.1
ENV JMETER_NAME apache-jmeter-$JMETER_VERSION
ENV JMETER_BIN_URL http://ftp.halifax.rwth-aachen.de/apache/jmeter/binaries/$JMETER_NAME.zip
ENV JMETER_TMP_DL_PATH /tmp/jmeter.tgz
ENV JMETER_DL_DEST_PATH $PLUGIN_PATH/download

RUN apk add openjdk11-jre-headless

RUN mkdir -p $JMETER_DL_DEST_PATH &&\
    wget -q $JMETER_BIN_URL -O $JMETER_TMP_DL_PATH &&\
    unzip -q $JMETER_TMP_DL_PATH -d $JMETER_DL_DEST_PATH
ENV PATH="$JMETER_DL_DEST_PATH/bin:$PATH"

