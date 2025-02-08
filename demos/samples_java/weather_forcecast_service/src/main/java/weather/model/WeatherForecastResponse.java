package weather.model;

import java.util.List;

public class WeatherForecastResponse {
    private String location;
    private String units;
    private List<DayForecast> forecast;

    // Default Constructor
    public WeatherForecastResponse() {}

    // Getters and Setters
    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getUnits() {
        return units;
    }

    public void setUnits(String units) {
        this.units = units;
    }

    public List<DayForecast> getDailyForecast() {
        return forecast;
    }

    public void setDailyForecast(List<DayForecast> forecast) {
        this.forecast = forecast;
    }
}
