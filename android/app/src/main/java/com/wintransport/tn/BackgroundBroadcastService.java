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
    private static final int NOTIFICATION_ID = 48211;
    private static volatile boolean running = false;

    private LocationManager locationManager;
    private ExecutorService networkExecutor;

    private String sessionId;
    private String lineId;
    private String direction;
    private String lineShortName;
    private String supabaseUrl;
    private String supabaseAnonKey;

    private long lastPublishAtMs = 0L;

    public static boolean isRunning() {
        return running;
    }

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
        final String vehicleLabel = ((lineShortName != null && !lineShortName.isEmpty()) ? lineShortName : "Ligne") + " (Signal direct)";

        networkExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject payload = new JSONObject();
                payload.put("id", sessionId);
                payload.put("line_id", lineId);
                payload.put("direction", direction);
                payload.put("vehicle_label", vehicleLabel);
                payload.put("latitude", latitude);
                payload.put("longitude", longitude);
                payload.put("heading", heading);
                payload.put("speed_kmh", speedKmh);
                payload.put("passenger_count", 1);
                payload.put("is_simulated", false);

                URL url = new URL(supabaseUrl + "/rest/v1/transit_live_locations");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(12000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setRequestProperty("apikey", supabaseAnonKey);
                connection.setRequestProperty("Authorization", "Bearer " + supabaseAnonKey);
                connection.setRequestProperty("Prefer", "resolution=merge-duplicates,return=minimal");

                byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream outputStream = connection.getOutputStream()) {
                    outputStream.write(body);
                }

                int code = connection.getResponseCode();
                if (code >= 400) {
                    Log.e(TAG, "Supabase push failed with HTTP " + code);
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
