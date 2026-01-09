set dotenv-load
set dotenv-filename := "config/.env"

default:
    @just -l

help:
    @just -l

commit MESSAGE PUSH="false" ORIGIN="origin" BRANCH="main":
    @echo "{{ MESSAGE }} | {{ ORIGIN }} | {{ BRANCH }}"

    @git add .
    @git commit -m "{{ MESSAGE }}"

    @echo "Changes commited with message:"
    @echo "{{ MESSAGE }}"

    if [[ "{{ PUSH }}" == "push" ]]; then \
        echo "Pushing changes to {{ ORIGIN }}/{{ BRANCH }}"; \
        git push {{ ORIGIN }} {{ BRANCH }}; \
    fi
