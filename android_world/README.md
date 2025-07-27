# UI-NEXUS


UI-NEXUS provides a comprehensive benchmark for compositional mobile device operation tasks. UI-NEXUS supports interactive evaluation in 20 fully controllable local utility app environments, as well as 30 online Chinese and English service apps. It comprises 100 interactive task templates with an average optimal step count of 14.05. 

See introduction videos on our [website](https://ui-nexus.github.io/).


## Dependency Management

It's recommended to use `conda`, which you can download [here](https://docs.anaconda.com/free/miniconda/miniconda-install/).

    ```
    conda create -n ui-nexus python=3.11.8
    conda activate ui-nexus
    ```

Then, you can install all the required packages by:

    ```
    pip install -r requirements.txt
    ```

## Set up Android Emulator with Local Utility Apps

The subset on local utility app environments, named as UI-NEXUS-Anchor, is developed by enhancing the task difficulty based on AndroidWorld benchmark. We adopt the same 20 apps as AndroidWorld and design more sophisticated task instruction templates with comprehensive coverage of task dependency structures. 

The infrastructure is mainly adapted from [AndroidWorld](https://github.com/google-research/android_world) and its [adaption in SPA-Bench](https://github.com/ai-agents-2030-modules/android_world/tree/d333bb099159a658dc0f9fd3bdc8a489b5e565f0).


### Installation

1. Set up the Android Emulator
   1. Download Android Studio [here](https://developer.android.com/studio?gad_source=1&gclid=Cj0KCQjw3ZayBhDRARIsAPWzx8oLcadBD0vAq8xmUutaunLGSzhgEtLz4xVZ_SpV4G0xJazS7LxQkDsaAuveEALw_wcB&gclsrc=aw.ds)
   2. Create an Android Virtual Device (AVD) by following these instructions. For hardware select **Pixel 6**, for System Image select **Tiramisu, API Level 33**, and choose AVD name as **AndroidWorldAvd**. [Watch the setup video.](https://github.com/google-research/android_world/assets/162379927/efc33980-8b36-44be-bb2b-a92d4c334a50)

1. Launch the Android Emulator from the command line

    Launch the emulator from the command line, not using the Android Studio UI, with the `-grpc 8554` flag which is needed communication with accessibility forwarding app.

    ```bash
    # Typically it's located in ~/Android/Sdk/emulator/emulator or
    # ~/Library/Android/sdk/emulator/emulator
    EMULATOR_NAME=AndroidWorldAvd # From previous step
    ~/Library/Android/sdk/emulator/emulator -avd $EMULATOR_NAME -no-snapshot -grpc 8554
    ```


1. Install the latest [AndroidEnv](https://github.com/google-deepmind/android_env):

    ```python
    git clone https://github.com/google-deepmind/android_env.git
    cd android_env
    python setup.py install
    ```

1. Run the setup script of AndroidWorld to automatically install necessary apps.

    ```python
    python setup.py install
    ```

1. Desktop Setup
   
   To minimize the impact of the app launching process on the test results, we placed all the app icons on the home screen during the tests. We install lawnchair[https://github.com/LawnchairLauncher/lawnchair] on the emulator, use lawnchair as the default launcher, and changed the desktop grid to 5x4 to exactly fit in the 20 local utility apps. 



### Environment Setup
We have developed a user-friendly script for Android emulator environment setup. You can configure the states of 20 local utility apps by simply writing json files.

More details are elaborated in [emulator_init/README.md](emulator_init/README.md)

The configurations files of UI-NEXUS-Anchor are in [emulator_init/README.md](emulator_init/README.md). Currently some representative cinfiguration files are provided. Complete configuration files will be released soon.


## Run the Agents

We are working on restructuring the code for a unified interface of all agents involved. 

