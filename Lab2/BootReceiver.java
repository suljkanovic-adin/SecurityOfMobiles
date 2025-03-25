package com.example.comadinsuljkanovicmyfirstapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        // Log the action to confirm the receiver is triggered
        Log.d("MyApp", "BootReceiver onReceive called with action: " + intent.getAction());

        // Safely compare the action string to avoid a potential NullPointerException
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Log.d("MyApp", "Device rebooted! BootReceiver triggered for ACTION_BOOT_COMPLETED.");
        }
    }
}
