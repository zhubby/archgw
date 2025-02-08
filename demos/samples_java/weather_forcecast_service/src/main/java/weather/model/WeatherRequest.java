package weather.model;

public class WeatherRequest {
    private String location;
    private int days = 7;
    private String units = "Farenheit";

    public WeatherRequest() {}

    // Getters and setters
    public String getLocation() {
        return location;
    }
    public void setLocation(String location) {
        this.location = location;
    }
    public int getDays() {
        return days;
    }
    public void setDays(int days) {
        this.days = days;
    }
    public String getUnits() {
        return units;
    }
    public void setUnits(String units) {
        this.units = units;
    }
}
