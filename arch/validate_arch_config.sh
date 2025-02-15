#!/bin/bash

failed_files=()

for file in $(find . -name arch_config.yaml -o -name arch_config_full_reference.yaml); do
  echo "Validating $file..."
  if ! docker run --rm -v "$(pwd)/$file:/app/arch_config.yaml:ro" --entrypoint /bin/sh katanemo/archgw:latest -c "python config_generator.py" 2>&1 > /dev/null ; then
    echo "Validation failed for $file"
    failed_files+=("$file")
  fi
done

# Print summary of failed files
if [ ${#failed_files[@]} -ne 0 ]; then
  echo -e "\nValidation failed for the following files:"
  printf '%s\n' "${failed_files[@]}"
  exit 1
else
  echo -e "\nAll files validated successfully!"
fi
