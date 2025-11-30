import json
from pathlib import Path
from PIL import Image

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications.mobilenet_v2 import (
    preprocess_input,
    MobileNetV2,
)
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Paths
DATA_DIR = Path("data")
TRAIN_DIR = DATA_DIR / "train"
VAL_DIR = DATA_DIR / "val"
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 12  # slightly more for multi-class

MODEL_PATH = MODELS_DIR / "biosense_classifier.h5"
CLASS_NAMES_PATH = MODELS_DIR / "class_names.json"


# 🧹 Remove corrupted images BEFORE TensorFlow loads dataset
def clean_invalid_images(directory: Path):
    removed = 0
    print(f"\n🔍 Checking: {directory}")
    for class_dir in directory.iterdir():
        if class_dir.is_dir():
            for img_path in class_dir.iterdir():
                if img_path.is_file():
                    try:
                        with Image.open(img_path) as img:
                            img.verify()
                    except Exception:
                        print(f"❌ Removed corrupted: {img_path}")
                        img_path.unlink(missing_ok=True)
                        removed += 1
    print(f"🧽 Clean finished — {removed} images removed")


# 📂 Load dataset safely (works for ANY class names present)
def load_datasets():
    raw_train_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        label_mode="categorical",
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    raw_val_ds = tf.keras.utils.image_dataset_from_directory(
        VAL_DIR,
        label_mode="categorical",
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    class_names = raw_train_ds.class_names
    print("📌 Classes:", class_names)

    # Save for inference + frontend
    with open(CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f)

    def safe_preprocess(image, label):
        image = tf.image.resize(image, IMAGE_SIZE)
        image = preprocess_input(image)
        return image, label

    train_ds = (
        raw_train_ds.map(safe_preprocess)
        .cache()
        .prefetch(tf.data.AUTOTUNE)
        .ignore_errors()
    )
    val_ds = (
        raw_val_ds.map(safe_preprocess)
        .cache()
        .prefetch(tf.data.AUTOTUNE)
        .ignore_errors()
    )

    return train_ds, val_ds, len(class_names)


# 🧠 Build Model
def build_model(num_classes: int):
    base_model = MobileNetV2(
        include_top=False,
        input_shape=IMAGE_SIZE + (3,),
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = layers.Input(shape=IMAGE_SIZE + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs, outputs)
    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# 🚀 Execute Training
def main():
    print("\n🧹 Cleaning dataset…")
    clean_invalid_images(TRAIN_DIR)
    clean_invalid_images(VAL_DIR)

    print("\n📥 Loading dataset...")
    train_ds, val_ds, num_classes = load_datasets()

    print("\n🧠 Building model...")
    model = build_model(num_classes)

    # callbacks for better training
    checkpoint_cb = ModelCheckpoint(
        filepath=str(MODEL_PATH),
        save_best_only=True,
        monitor="val_accuracy",
        mode="max",
        verbose=1,
    )
    early_stop_cb = EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1,
    )

    print("\n🚀 Training…")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[checkpoint_cb, early_stop_cb],
    )

    print("\n💾 Saving final model...")
    model.save(MODEL_PATH)
    print(f"✔ Model saved: {MODEL_PATH}")
    print(f"✔ Classes saved: {CLASS_NAMES_PATH}")
    print("\n🎉 Training Completed Successfully!")


if __name__ == "__main__":
    main()
