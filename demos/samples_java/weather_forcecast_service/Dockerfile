# Stage 1: Build the application using Maven
FROM maven:3.8.7-openjdk-18-slim AS build
WORKDIR /app
# Copy pom.xml and download dependencies first (caching)
COPY pom.xml .
RUN mvn dependency:go-offline
# Copy the source code and build the application
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Run the application using a slim JDK image
FROM openjdk:17-jdk-slim
WORKDIR /app
# Copy the built jar from the previous stage
COPY --from=build /app/target/weather-forecast-service-0.0.1-SNAPSHOT.jar app.jar
# Expose the port on which the app runs (default Spring Boot is 8080)
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
