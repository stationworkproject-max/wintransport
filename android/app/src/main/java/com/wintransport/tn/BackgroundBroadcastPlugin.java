package com.wintransport.tn;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;

import androidx.core.content.ContextCompat;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "BackgroundBroadcast")
public class BackgroundBroadcastPlugin extends Plugin {

    @PluginMethod
    public void start(PluginCall call) {
        String sessionId = call.getString("sessionId");
        String lineId = call.getString("lineId");
        String direction = call.getString("direction");
        String lineShortName = call.getString("lineShortName", "Ligne");
        String broadcasterId = call.getString("broadcasterId", sessionId);
        String supabaseUrl = call.getString("supabaseUrl");
        String supabaseAnonKey = call.getString("supabaseAnonKey");

        if (sessionId == null || lineId == null || direction == null || supabaseUrl == null || supabaseAnonKey == null) {
            call.reject("Missing required start parameters.");
            return;
        }

        boolean hasFine = ContextCompat.checkSelfPermission(getContext(), Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED;
        boolean hasCoarse = ContextCompat.checkSelfPermission(getContext(), Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
        if (!hasFine && !hasCoarse) {
            call.reject("Location permission is missing. Please grant GPS access first.");
            return;
        }

        Intent serviceIntent = new Intent(getContext(), BackgroundBroadcastService.class);
        serviceIntent.setAction(BackgroundBroadcastService.ACTION_START);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_SESSION_ID, sessionId);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_BROADCASTER_ID, broadcasterId);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_LINE_ID, lineId);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_DIRECTION, direction);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_LINE_SHORT_NAME, lineShortName);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_SUPABASE_URL, supabaseUrl);
        serviceIntent.putExtra(BackgroundBroadcastService.EXTRA_SUPABASE_ANON_KEY, supabaseAnonKey);

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                ContextCompat.startForegroundService(getContext(), serviceIntent);
            } else {
                getContext().startService(serviceIntent);
            }

            JSObject result = new JSObject();
            result.put("started", true);
            result.put("running", true);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Unable to start background broadcast service.", e);
        }
    }

    @PluginMethod
    public void stop(PluginCall call) {
        Intent serviceIntent = new Intent(getContext(), BackgroundBroadcastService.class);
        serviceIntent.setAction(BackgroundBroadcastService.ACTION_STOP);

        boolean stopped;
        try {
            stopped = getContext().stopService(serviceIntent);
        } catch (Exception e) {
            call.reject("Unable to stop background broadcast service.", e);
            return;
        }

        JSObject result = new JSObject();
        result.put("stopped", stopped || !BackgroundBroadcastService.isRunning());
        result.put("running", BackgroundBroadcastService.isRunning());
        call.resolve(result);
    }

    @PluginMethod
    public void isRunning(PluginCall call) {
        JSObject result = new JSObject();
        result.put("running", BackgroundBroadcastService.isRunning());
        call.resolve(result);
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject result = new JSObject();
        result.put("running", BackgroundBroadcastService.isRunning());
        result.put("speed", BackgroundBroadcastService.getLastSpeed());
        result.put("latitude", BackgroundBroadcastService.getLastLatitude());
        result.put("longitude", BackgroundBroadcastService.getLastLongitude());
        call.resolve(result);
    }

    @PluginMethod
    public void openLocationSettings(PluginCall call) {
        try {
            Intent intent = new Intent(android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            JSObject result = new JSObject();
            result.put("opened", true);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Could not open location settings", e);
        }
    }

    @PluginMethod
    public void openAppSettings(PluginCall call) {
        try {
            Intent intent = new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(android.net.Uri.fromParts("package", getContext().getPackageName(), null));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            JSObject result = new JSObject();
            result.put("opened", true);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Could not open app settings", e);
        }
    }

    @PluginMethod
    public void isLocationEnabled(PluginCall call) {
        try {
            android.location.LocationManager lm = (android.location.LocationManager) getContext().getSystemService(android.content.Context.LOCATION_SERVICE);
            boolean isGpsEnabled = false;
            boolean isNetworkEnabled = false;
            if (lm != null) {
                isGpsEnabled = lm.isProviderEnabled(android.location.LocationManager.GPS_PROVIDER);
                isNetworkEnabled = lm.isProviderEnabled(android.location.LocationManager.NETWORK_PROVIDER);
            }
            JSObject result = new JSObject();
            result.put("enabled", isGpsEnabled || isNetworkEnabled);
            result.put("gpsEnabled", isGpsEnabled);
            result.put("networkEnabled", isNetworkEnabled);
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Error checking location status", e);
        }
    }
}
