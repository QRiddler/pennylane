# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

From pennylane/base:latest
ARG PLUGIN_NAME=tensorflow
WORKDIR /opt/pennylane/docker/plugins
RUN chmod +x install-plugin.sh && ./install-plugin.sh $PLUGIN_NAME
# Run Unit-Tests again
WORKDIR /opt/pennylane
RUN make test
# Image build completed.
CMD echo "Successfully built Docker image"
