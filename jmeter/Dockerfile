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

RUN apk add openjdk11-jre-headless

RUN wget -q $JMETER_BIN_URL -O $JMETER_TMP_DL_PATH &&\
    unzip -q $JMETER_TMP_DL_PATH -d $PLUGIN_PATH
ENV PATH="$PLUGIN_PATH/$JMETER_NAME/bin:$PATH"

