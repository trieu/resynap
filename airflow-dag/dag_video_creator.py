from airflow import DAG
from airflow.operators.python import PythonOperator


from datetime import datetime, timedelta
import os
from video_creator_util import VideoGenerator
import logging

logger = logging.getLogger('video_creation_dag')

# Define default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}


def generate_video_ok(**kwargs):
   
    conf = kwargs['dag_run'].conf
    output_path = conf.get('output_path')    
    
     # TODO: Implement the logic to send the video to the user
    # For now, we'll just log the output path
    logger.info(f"✅ Video successfully created: {output_path}")

# Define the function to run video creation


def generate_video(**kwargs):
    # Extract parameters from the DAG run configuration 
    conf = kwargs['dag_run'].conf
    script_content = conf.get('script_content')    
    video_filename = conf.get('video_filename')    
    logger.info('generate_video...')
    logger.info('script_content ' + script_content)
    logger.info('video_filename ' + video_filename)
    
    try:
        output_path = f"./resources/generated_videos/{video_filename}"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        video_generator = VideoGenerator(script_content, output_path)
        video_generator.run()

        logger.info(f"✅ Video successfully created: {output_path}")
        conf.update({'output_path': output_path})

    except Exception as e:
        logger.info(f"❌ Video generation failed: {e}")
        raise e  # Ensure Airflow marks this task as failed


# Define the DAG
with DAG(
    dag_id="video_creation_dag",
    default_args=default_args,
    schedule_interval=None,  # Manually triggered or can be set to a cron schedule
    catchup=False,
    dagrun_timeout=timedelta(minutes=60),
    tags=["CDP Profile Enrichment"],
    params={"script_content": "", "video_filename": ""},
) as dag:

    generate_video_task = PythonOperator(
        task_id="generate_video", python_callable=generate_video, provide_context=True
    )

    generate_video_ok = PythonOperator(
        task_id='generate_video_ok', python_callable=generate_video_ok, provide_context=True
    )

# Task flow
generate_video_task >> generate_video_ok
