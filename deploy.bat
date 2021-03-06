@echo off
ECHO Running deploy commands...

SET PROJECT_ID=brainfuck-linebot
SET IMAGE_NAME=bot
SET SERVICE_NAME=%IMAGE_NAME%

CMD /c gcloud builds submit --tag gcr.io/%PROJECT_ID%/%IMAGE_NAME%
REM gcloud run deploy --image gcr.io/%PROJECT_ID%/%IMAGE_NAME% --platform managed
CMD /c gcloud run services update %SERVICE_NAME% --image gcr.io/%PROJECT_ID%/%IMAGE_NAME%:latest --platform=managed --region=asia-east1

ECHO succeeded!