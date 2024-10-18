package com.example.streetsmart

// This file has a lot of vestigial code

import kotlin.math.*
import android.Manifest
import android.annotation.SuppressLint
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
//import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.platform.LocalContext
import com.google.android.gms.location.*
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import android.content.ContentValues
//import android.content.Context
import android.provider.MediaStore
import java.io.OutputStreamWriter
import android.util.Log
import androidx.compose.foundation.background
//import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

import android.content.Intent
import android.app.Activity

import android.content.Context
import android.os.Environment
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import java.io.File



fun haversine(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
    val R = 6371000.0 // Earth's radius in meters
    val dLat = Math.toRadians(lat2 - lat1)
    val dLon = Math.toRadians(lon2 - lon1)
    val a = sin(dLat / 2) * sin(dLat / 2) + cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLon / 2) * sin(dLon / 2)
    val c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
}

fun saveData(context: Context, fileName: String, text: String) {
    val contentResolver = context.contentResolver

    // Query for the existing file
    val projection = arrayOf(MediaStore.Files.FileColumns._ID)
    val selection = "${MediaStore.Files.FileColumns.DISPLAY_NAME} = ?"
    val selectionArgs = arrayOf(fileName)

    val cursor = contentResolver.query(
        MediaStore.Files.getContentUri("external"),
        projection,
        selection,
        selectionArgs,
        null
    )

    if (cursor?.moveToFirst() == true) {
        // File exists, get the URI
        val id = cursor.getLong(cursor.getColumnIndexOrThrow(MediaStore.Files.FileColumns._ID))
        val uri = MediaStore.Files.getContentUri("external").buildUpon().appendPath(id.toString()).build()

        // Open the file for appending
        contentResolver.openOutputStream(uri, "wa")?.use { outputStream ->
            OutputStreamWriter(outputStream).apply {
                append(text)
                flush()
            }
        } ?: run {
            Log.e("File Write", "Failed to open the file for appending.")
        }
    } else {
        // File does not exist, create a new one
        val values = ContentValues().apply {
            put(MediaStore.Files.FileColumns.DISPLAY_NAME, fileName)
            put(MediaStore.Files.FileColumns.MIME_TYPE, "text/plain")
            put(MediaStore.Files.FileColumns.RELATIVE_PATH, "Documents/StreetSmart/")
        }

        val uri = contentResolver.insert(MediaStore.Files.getContentUri("external"), values)
        uri?.let {
            contentResolver.openOutputStream(it)?.use { outputStream ->
                outputStream.write(text.toByteArray())
            }
        } ?: run {
            Log.e("File Write", "Failed to create the file.")
        }
    }

    cursor?.close()
}

class MainActivity : ComponentActivity(), SensorEventListener {
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null

    // Expose the current time as a mutable state
    private var accelerometerData by mutableStateOf(Triple(0f, 0f, 0f))
    private var acc_time by mutableStateOf(-1L)
    private var currentTime by mutableStateOf("")
    private var instantTime by mutableStateOf(-1L)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Start the AccelerometerService
        Intent(this, AccelerometerService::class.java).also { intent ->
            startService(intent)
        }

        // Set up the UI content using Jetpack Compose
        setContent {
            DisplayDataAndButtons(
                latitudeState = latitudeState.value,
                longitudeState = longitudeState.value,
                currentTime = currentTime,
                instantTime = instantTime,
                accelerometerData = accelerometerData,
                acc_time = acc_time
            )
        }

        // Initialize the FusedLocationProviderClient
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        requestPermissions()

        // Initialize SensorManager and Accelerometer
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)

        // Listener for the Accelerometer
        accelerometer?.also { sensor ->
            sensorManager.registerListener(
                this,
                sensor,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
    }

    @SuppressLint("MissingPermission")
    private fun requestPermissions() { // Request location permissions from user
        val locationPermissionRequest = registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { isGranted: Boolean ->
            if (isGranted) {
                getLocationUpdates() // Begin getting location updates
            }
        }

        locationPermissionRequest.launch(Manifest.permission.ACCESS_FINE_LOCATION)
    }

    @SuppressLint("MissingPermission")
    private fun getLocationUpdates() {
        val locationRequest = LocationRequest.create().apply {
            interval = 1000 // Update every second
            fastestInterval = 500 // Fastest interval is 0.5 seconds
            priority = LocationRequest.PRIORITY_HIGH_ACCURACY
        }

        fusedLocationClient.requestLocationUpdates(locationRequest, object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                val location = locationResult.lastLocation // Get last known location
                val instance = LocalDateTime.now() // Get current time

                location?.let {
                    latitudeState.value = it.latitude
                    longitudeState.value = it.longitude
                }
                instance.let {
                    currentTime = instance.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) // Format date
                    instantTime = System.currentTimeMillis() // Current instance
                }
            }
        }, mainLooper)
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            val x = event.values[0]
            val y = event.values[1]
            val z = event.values[2]

            // Update accelerometer data
            accelerometerData = Triple(x, y, z)
            acc_time = System.currentTimeMillis()
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        // Can be left empty
    }

    companion object {
        // Variables for location and time
        var latitudeState = mutableStateOf(0.0)
        var longitudeState = mutableStateOf(0.0)
    }
}

@Composable
fun DisplayDataAndButtons(
    latitudeState: Double,
    longitudeState: Double,
    currentTime: String,
    instantTime: Long,
    accelerometerData: Triple<Float, Float, Float>,
    acc_time: Long
) {
    val context = LocalContext.current
    var showConfirmationDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(30.dp)
            .background(Color.Black)
    ) {
        Text(text = "GPS Module:" , fontSize = 32.sp, color = Color.Red)
        Text(text = "Latitude: $latitudeState", fontSize = 24.sp, color = Color.Green)
        Text(text = "Longitude: $longitudeState", fontSize = 24.sp, color = Color.Green)
        Text(text = "Instant Time: $instantTime", fontSize = 24.sp, color = Color.Green)
        Text(text = "Last Update:\n $currentTime\n\n", fontSize = 18.sp, color = Color.Blue)
        Text(text = "Accelerometer Module:" , fontSize = 32.sp, color = Color.Red)
        Text(text = "Accelerometer Data:\nX: ${accelerometerData.first}\nY: ${accelerometerData.second}\nZ: ${accelerometerData.third}", fontSize = 24.sp , color = Color.Green)
        Text(text = "Accelerometer Time: $acc_time", fontSize = 24.sp , color = Color.Green)

        val context = LocalContext.current
        var saveText = "L:$latitudeState,$longitudeState,$instantTime;A:${accelerometerData.first},${accelerometerData.second},${accelerometerData.third},$acc_time;\n"
        saveData(context, "streetsmart_data_alpha.txt", saveText)

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = {
                // Exit the application
                (context as? Activity)?.finish()
            },
            colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
        ) {
            Text("Exit Application", color = Color.White)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = { showConfirmationDialog = true },
            colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
        ) {
            Text("Clear collected data", color = Color.White)
        }
    }

    if (showConfirmationDialog) {
        ConfirmationDialog(
            onConfirm = {
                clearData(context)
                showConfirmationDialog = false
            },
            onDismiss = { showConfirmationDialog = false }
        )
    }
}

@Composable
fun DataClearScreen() {
    val context = LocalContext.current
    var showConfirmationDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Button(
            onClick = { showConfirmationDialog = true },
            colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
        ) {
            Text("Clear collected data")
        }
    }

    if (showConfirmationDialog) {
        ConfirmationDialog(
            onConfirm = {
                clearData(context)
                showConfirmationDialog = false
            },
            onDismiss = { showConfirmationDialog = false }
        )
    }
}

@Composable
fun ConfirmationDialog(onConfirm: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Confirm Data Deletion") },
        text = { Text("Are you sure you want to clear all collected data? This action cannot be undone.") },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
            ) {
                Text("Confirm" , color = Color.Black)
            }
        },
        dismissButton = {
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = Color.Green)
                ) {
                Text("Cancel" , color = Color.Black)
            }
        }
    )
}

fun clearData(context: Context) {
    val file = File(
        context.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS),
        "StreetSmart/streetsmart_data_alpha.txt"
    )
    if (file.exists()) {
        file.writeText("") // Clear the file content
    }
}