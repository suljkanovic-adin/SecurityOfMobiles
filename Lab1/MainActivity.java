package com.example.comadinsuljkanovicmyfirstapp;

import androidx.appcompat.app.AppCompatActivity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;

/**
 * A simple MainActivity in Java.
 * This Activity has two buttons:
 * 1) One to start a background Service.
 * 2) One to send a custom broadcast.
 */
public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Button that starts the Service
        Button btnStartService = findViewById(R.id.btn_start_service);
        btnStartService.setOnClickListener(view -> {
            // This starts our MyService in the background
            Intent serviceIntent = new Intent(MainActivity.this, MyService.class);
            startService(serviceIntent);
        });

        // Button that sends a custom broadcast
        Button btnSendBroadcast = findViewById(R.id.btn_send_broadcast);
        btnSendBroadcast.setOnClickListener(view -> {
            Intent broadcastIntent = new Intent(MainActivity.this, MyBroadcastReceiver.class);
            broadcastIntent.setAction("com.adinsuljkanovic.myfirstapp.CUSTOM_BROADCAST");
            sendBroadcast(broadcastIntent);

        });
    }
}