package com.example.streetsmart

import android.app.Service
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.IBinder
import android.util.Log

class AccelerometerService : Service(), SensorEventListener {
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null

    override fun onCreate() {
        super.onCreate()
        // Initialize the SensorManager and the accelerometer
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        // Register the listener for the accelerometer
        accelerometer?.let { sensor ->
            sensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL)
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            val x = event.values[0]
            val y = event.values[1]
            val z = event.values[2]

            // Log the accelerometer data or handle it as needed
            Log.d("AccelerometerService", "X: $x, Y: $y, Z: $z")
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // Can be left empty
    }

    override fun onBind(intent: Intent?): IBinder? {
        // This is a started service; binding is not used
        return null
    }

    override fun onDestroy() {
        super.onDestroy()
        // Unregister the listener when the service is destroyed
        sensorManager.unregisterListener(this)
    }
}
