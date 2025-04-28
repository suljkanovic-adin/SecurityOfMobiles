#include <jni.h>

static jstring getUrl(JNIEnv* env, jobject /* this */) {
    return env->NewStringUTF("https://google.com");
}

static JNINativeMethod methods[] = {
        {"getUrlFromNative","()Ljava/lang/String;",(void*)getUrl}
};

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* /*reserved*/) {
    JNIEnv* env;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK)
        return -1;
    jclass clazz = env->FindClass("com/example/nativeurlapp/MainActivity");
    if (!clazz || env->RegisterNatives(clazz, methods, 1) < 0)
        return -1;
    return JNI_VERSION_1_6;
}
