package com.wintransport.tn;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class BackgroundBroadcastService extends Service {
    public static final String ACTION_START = "com.wintransport.tn.action.START_BACKGROUND_BROADCAST";
    public static final String ACTION_STOP = "com.wintransport.tn.action.STOP_BACKGROUND_BROADCAST";

    public static final String EXTRA_SESSION_ID = "sessionId";
    public static final String EXTRA_LINE_ID = "lineId";
    public static final String EXTRA_DIRECTION = "direction";
    public static final String EXTRA_LINE_SHORT_NAME = "lineShortName";
    public static final String EXTRA_SUPABASE_URL = "supabaseUrl";
    public static final String EXTRA_SUPABASE_ANON_KEY = "supabaseAnonKey";

    private static final String TAG = "BgBroadcastService";
    private static final String CHANNEL_ID = "bg_broadcast_location";
    private static volatile boolean running = false;
    private static volatile int lastSpeedKmh = 0;
    private static volatile double lastLatitude = 0.0;
    private static volatile double lastLongitude = 0.0;

    public static boolean isRunning() {
        return running;
    }

    public static int getLastSpeed() {
        return lastSpeedKmh;
    }

    public static double getLastLatitude() {
        return lastLatitude;
    }

    public static double getLastLongitude() {
        return lastLongitude;
    }

    private static final int NOTIFICATION_ID = 48211;

    private LocationManager locationManager;
    private ExecutorService networkExecutor;

    private String sessionId;
    private String lineId;
    private String direction;
    private String lineShortName;
    private String supabaseUrl;
    private String supabaseAnonKey;

    private long lastPublishAtMs = 0L;

    private final LocationListener locationListener = new LocationListener() {
        @Override
        public void onLocationChanged(@NonNull Location location) {
            publishLocation(location);
        }

        @Override
        public void onProviderDisabled(@NonNull String provider) {
        }

        @Override
        public void onProviderEnabled(@NonNull String provider) {
        }

        @Override
        public void onStatusChanged(String provider, int status, Bundle extras) {
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        networkExecutor = Executors.newSingleThreadExecutor();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }

        if (intent != null) {
            sessionId = intent.getStringExtra(EXTRA_SESSION_ID);
            lineId = intent.getStringExtra(EXTRA_LINE_ID);
            direction = intent.getStringExtra(EXTRA_DIRECTION);
            lineShortName = intent.getStringExtra(EXTRA_LINE_SHORT_NAME);
            supabaseUrl = intent.getStringExtra(EXTRA_SUPABASE_URL);
            supabaseAnonKey = intent.getStringExtra(EXTRA_SUPABASE_ANON_KEY);
        }

        if (sessionId == null || lineId == null || direction == null || supabaseUrl == null || supabaseAnonKey == null) {
            Log.e(TAG, "Missing required broadcast extras, stopping service.");
            stopSelf();
            return START_NOT_STICKY;
        }

        startForeground(NOTIFICATION_ID, buildNotification());
        startLocationUpdates();
        running = true;
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        stopLocationUpdates();
        running = false;

        final String sId = sessionId;
        final String sUrl = supabaseUrl;
        final String sKey = supabaseAnonKey;
        if (sId != null && sUrl != null && sKey != null) {
            new Thread(() -> {
                try {
                    JSONObject leavePayload = new JSONObject();
                    leavePayload.put("p_vehicle_id", sId);
                    leavePayload.put("p_broadcaster_id", sId);
                    URL url = new URL(sUrl + "/rest/v1/rpc/broadcast_leave");
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setConnectTimeout(3000);
                    conn.setReadTimeout(3000);
                    conn.setDoOutput(true);
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setRequestProperty("apikey", sKey);
                    conn.setRequestProperty("Authorization", "Bearer " + sKey);
                    byte[] b = leavePayload.toString().getBytes(StandardCharsets.UTF_8);
                    conn.setFixedLengthStreamingMode(b.length);
                    try (OutputStream os = conn.getOutputStream()) { os.write(b); }
                    conn.getResponseCode();
                    conn.disconnect();
                } catch (Exception ignored) {}
            }).start();
        }

        if (networkExecutor != null) {
            networkExecutor.shutdownNow();
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE);
        } else {
            stopForeground(true);
        }

        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private boolean hasLocationPermission() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void startLocationUpdates() {
        if (!hasLocationPermission()) {
            Log.e(TAG, "Location permission missing. Stopping foreground service.");
            stopSelf();
            return;
        }

        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 3000L, 3f, locationListener);
            }
        } catch (SecurityException e) {
            Log.e(TAG, "Cannot request GPS updates", e);
        }

        try {
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 3000L, 3f, locationListener);
            }
        } catch (SecurityException e) {
            Log.e(TAG, "Cannot request network location updates", e);
        }
    }

    private void stopLocationUpdates() {
        if (locationManager == null) return;
        try {
            locationManager.removeUpdates(locationListener);
        } catch (SecurityException ignored) {
        }
    }

    private void publishLocation(Location location) {
        if (location == null) return;

        long now = System.currentTimeMillis();
        if (now - lastPublishAtMs < 3500L) {
            return;
        }
        lastPublishAtMs = now;

        final double latitude = location.getLatitude();
        final double longitude = location.getLongitude();
        final double heading = location.hasBearing() ? location.getBearing() : 0d;
        final int speedKmh = location.hasSpeed() ? Math.max(0, Math.round(location.getSpeed() * 3.6f)) : 0;
        lastLatitude = latitude;
        lastLongitude = longitude;
        lastSpeedKmh = speedKmh;
        final String vehicleLabel = ((lineShortName != null && !lineShortName.isEmpty()) ? lineShortName : "Ligne") + " (Signal direct)";
        final int dirInt = "1".equals(direction) ? 1 : 0;

        networkExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                // High-scale unlogged RPC lease payload
                JSONObject payload = new JSONObject();
                payload.put("p_vehicle_id", sessionId);
                payload.put("p_route_id", lineId);
                payload.put("p_line_name", lineShortName != null ? lineShortName : "");
                payload.put("p_direction", dirInt);
                payload.put("p_direction_name", direction != null ? direction : "");
                payload.put("p_lat", latitude);
                payload.put("p_lon", longitude);
                payload.put("p_speed", speedKmh);
                payload.put("p_bearing", heading);
                payload.put("p_broadcaster_id", sessionId);

                URL url = new URL(supabaseUrl + "/rest/v1/rpc/broadcast_ping");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(8000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setRequestProperty("apikey", supabaseAnonKey);
                connection.setRequestProperty("Authorization", "Bearer " + supabaseAnonKey);

                byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream outputStream = connection.getOutputStream()) {
                    outputStream.write(body);
                }

                int code = connection.getResponseCode();
                if (code == 404) {
                    // Fallback to legacy table if RPC is not yet created
                    if (connection != null) connection.disconnect();
                    JSONObject legPayload = new JSONObject();
                    legPayload.put("id", sessionId);
                    legPayload.put("line_id", lineId);
                    legPayload.put("direction", direction);
                    legPayload.put("vehicle_label", vehicleLabel);
                    legPayload.put("latitude", latitude);
                    legPayload.put("longitude", longitude);
                    legPayload.put("heading", heading);
                    legPayload.put("speed_kmh", speedKmh);
                    legPayload.put("passenger_count", 1);
                    legPayload.put("is_simulated", false);

                    URL legUrl = new URL(supabaseUrl + "/rest/v1/transit_live_locations");
                    connection = (HttpURLConnection) legUrl.openConnection();
                    connection.setRequestMethod("POST");
                    connection.setConnectTimeout(8000);
                    connection.setReadTimeout(8000);
                    connection.setDoOutput(true);
                    connection.setRequestProperty("Content-Type", "application/json");
                    connection.setRequestProperty("apikey", supabaseAnonKey);
                    connection.setRequestProperty("Authorization", "Bearer " + supabaseAnonKey);
                    connection.setRequestProperty("Prefer", "resolution=merge-duplicates,return=minimal");

                    byte[] legBody = legPayload.toString().getBytes(StandardCharsets.UTF_8);
                    connection.setFixedLengthStreamingMode(legBody.length);
                    try (OutputStream outputStream = connection.getOutputStream()) {
                        outputStream.write(legBody);
                    }
                    connection.getResponseCode();
                }
            } catch (Exception e) {
                Log.e(TAG, "Failed to publish background location", e);
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
        });
    }

    private Notification buildNotification() {
        Intent openAppIntent = getPackageManager().getLaunchIntentForPackage(getPackageName());
        PendingIntent pendingIntent = null;
        if (openAppIntent != null) {
            openAppIntent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                flags |= PendingIntent.FLAG_IMMUTABLE;
            }
            pendingIntent = PendingIntent.getActivity(this, 0, openAppIntent, flags);
        }

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setContentTitle("WinTransport TN")
                .setContentText("Diffusion en direct active même en arrière-plan")
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setPriority(NotificationCompat.PRIORITY_LOW);

        if (pendingIntent != null) {
            builder.setContentIntent(pendingIntent);
        }

        return builder.build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }

        NotificationManager notificationManager = getSystemService(NotificationManager.class);
        if (notificationManager == null) {
            return;
        }

        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Live Broadcast",
                NotificationManager.IMPORTANCE_LOW
        );
        channel.setDescription("Background location while broadcasting transit position");
        notificationManager.createNotificationChannel(channel);
    }
}
