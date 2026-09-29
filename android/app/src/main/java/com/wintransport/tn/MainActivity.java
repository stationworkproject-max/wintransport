package com.wintransport.tn;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(BackgroundBroadcastPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
