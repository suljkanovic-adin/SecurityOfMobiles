package com.example.comadinsuljkanovicmyfirstapp;

import androidx.appcompat.app.AppCompatActivity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import java.io.File;
import java.io.FileOutputStream;
import android.location.Location;
import android.location.LocationManager;
import android.util.Log;
import android.content.Context;
import java.io.IOException;
import android.Manifest;
import android.content.pm.PackageManager;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.os.AsyncTask;
import android.widget.TextView;
import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;


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

        // Before accessing location
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            // Permission is not granted, so request it
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                    1);  // 1 is the request code
        } else {
            // Permission already granted, get the location
            getLocation();
        }

        File file = new File(getExternalFilesDir(null), "testfile.txt");
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write("Hello from external storage!".getBytes());
        } catch (IOException e) {
            e.printStackTrace();
        }

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

        // Start fetching data from the Internet
        new FetchDataTask().execute("https://www.google.com");
    }

    private void getLocation() {
        // Lint requires a check right before using location APIs
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED
                && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            // Permission was somehow not granted, so just return or handle gracefully
            return;
        }

        LocationManager locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        Location location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
        Log.d("MyApp", "Location: " + location);
    }

    // Override to handle the result of the permission request
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 1) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // Permission granted, now get the location
                getLocation();
            } else {
                Log.d("MyApp", "Location permission denied.");
            }
        }
    }

    private class FetchDataTask extends AsyncTask<String, Void, String> {
        @Override
        protected String doInBackground(String... urls) {
            String result = "";
            HttpURLConnection connection = null;
            try {
                URL url = new URL(urls[0]);
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                InputStream in = new BufferedInputStream(connection.getInputStream());
                result = convertStreamToString(in);
                in.close();
            } catch (Exception e) {
                e.printStackTrace();
                result = "Error: " + e.getMessage();
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
            return result;
        }

        @Override
        protected void onPostExecute(String result) {
            // Display the result in the TextView
            TextView tvResult = findViewById(R.id.tvResult);
            tvResult.setText(result);
        }

        private String convertStreamToString(InputStream is) throws IOException {
            BufferedReader reader = new BufferedReader(new InputStreamReader(is));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append("\n");
            }
            reader.close();
            return sb.toString();
        }

    }

}