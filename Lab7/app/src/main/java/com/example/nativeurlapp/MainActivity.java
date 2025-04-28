package com.example.nativeurlapp;

import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    // Load the native library
    static {
        System.loadLibrary("native-lib");
    }

    // Declare the native method
    private native String getUrlFromNative();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Inflate the layout
        setContentView(R.layout.activity_main);

        // Find the TextView and call the native method
        TextView tv = findViewById(R.id.sample_text);
        String url = getUrlFromNative();     // call into native-lib.so
        tv.setText(url);
    }
}
