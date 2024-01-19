FROM postgres:15-alpine
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=TW_op_avail
COPY create_table.sql /docker-entrypoint-initdb.d/create_table.sql