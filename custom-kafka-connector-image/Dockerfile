FROM confluentinc/cp-kafka-connect:7.5.0

ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"

# Conector JDBC (PostgreSQL como source)
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.4

# Conector Amazon S3 (sink)
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-s3:10.5.7

# Driver JDBC do PostgreSQL no classpath do conector
RUN curl -fsSL -o /usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib/postgresql-42.7.3.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar
