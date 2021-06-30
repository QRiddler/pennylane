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

import pytest
import numpy as np

import pennylane as qml
from pennylane.wires import Wires
from pennylane.transforms.optimization import merge_rotations


class TestMergeRotations:
    """Test that adjacent rotation gates of the same type will add the angles."""

    @pytest.mark.parametrize(
        ("theta_1", "theta_2", "expected_ops"),
        [
            (0.3, -0.2, [qml.RZ(0.1, wires=0)]),
            (0.15, -0.15, []),
        ],
    )
    def test_one_qubit_rotation_merge(self, theta_1, theta_2, expected_ops):
        """Test that a single-qubit circuit with adjacent rotation along the same
        axis either merge, or cancel if the angles sum to 0."""

        def qfunc():
            qml.RZ(theta_1, wires=0)
            qml.RZ(theta_2, wires=0)

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == len(expected_ops)

        # Check that all operations and parameter values are as expected
        for op_obtained, op_expected in zip(ops, expected_ops):
            assert op_obtained.name == op_expected.name
            assert np.allclose(op_obtained.parameters, op_expected.parameters)

    @pytest.mark.parametrize(
        ("theta_1", "theta_2", "expected_ops"),
        [
            (0.3, -0.2, [qml.RZ(0.3, wires=0), qml.RZ(-0.2, wires=1)]),
            (0.15, -0.15, [qml.RZ(0.15, wires=0), qml.RZ(-0.15, wires=1)]),
        ],
    )
    def test_two_qubits_rotation_no_merge(self, theta_1, theta_2, expected_ops):
        """Test that a two-qubit circuit with rotations on different qubits
        do not get merged."""

        def qfunc():
            qml.RZ(theta_1, wires=0)
            qml.RZ(theta_2, wires=1)

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == len(expected_ops)

        for op_obtained, op_expected in zip(ops, expected_ops):
            assert op_obtained.name == op_expected.name
            assert np.allclose(op_obtained.parameters, op_expected.parameters)

    @pytest.mark.parametrize(
        ("theta_11", "theta_12", "theta_21", "theta_22", "expected_ops"),
        [
            (0.3, -0.2, 0.5, -0.8, [qml.RX(0.1, wires=0), qml.RY(-0.3, wires=1)]),
            (0.3, -0.3, 0.7, -0.1, [qml.RY(0.6, wires=1)]),
        ],
    )
    def test_two_qubits_rotation_no_merge(
        self, theta_11, theta_12, theta_21, theta_22, expected_ops
    ):
        """Test that a two-qubit circuit with rotations on different qubits get merged."""

        def qfunc():
            qml.RX(theta_11, wires=0)
            qml.RY(theta_21, wires=1)
            qml.RX(theta_12, wires=0)
            qml.RY(theta_22, wires=1)

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == len(expected_ops)

        for op_obtained, op_expected in zip(ops, expected_ops):
            assert op_obtained.name == op_expected.name
            assert np.allclose(op_obtained.parameters, op_expected.parameters)

    def test_one_qubits_rotation_blocked(self):
        """Test that rotations on one-qubit separated by a "blocking" operation don't merge."""

        def qfunc():
            qml.RX(0.5, wires=0)
            qml.Hadamard(wires=0)
            qml.RX(0.4, wires=0)

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == 3

        assert ops[0].name == "RX"
        assert ops[0].parameters[0] == 0.5

        assert ops[1].name == "Hadamard"

        assert ops[2].name == "RX"
        assert ops[2].parameters[0] == 0.4

    def test_two_qubits_rotation_blocked(self):
        """Test that rotations on a two-qubit system separated by a "blocking" operation
        don't merge."""

        def qfunc():
            qml.RX(-0.42, wires=0)
            qml.CNOT(wires=[0, 1])
            qml.RX(0.8, wires=0)

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == 3

        assert ops[0].name == "RX"
        assert ops[0].wires == Wires(0)
        assert ops[0].parameters[0] == -0.42

        assert ops[1].name == "CNOT"
        assert ops[1].wires == Wires([0, 1])

        assert ops[2].name == "RX"
        assert ops[2].wires == Wires(0)
        assert ops[2].parameters[0] == 0.8

    def test_controlled_rotation_merge(self):
        """Test that adjacent controlled rotations on the same wires in same order get merged."""

        def qfunc():
            qml.CRY(0.2, wires=["w1", "w2"])
            qml.CRY(0.3, wires=["w1", "w2"])

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == 1

        assert ops[0].name == "CRY"
        assert ops[0].wires == Wires(["w1", "w2"])
        assert ops[0].parameters[0] == 0.5

    def test_controlled_rotation_no_merge(self):
        """Test that adjacent controlled rotations on the same wires in different order don't merge."""

        def qfunc():
            qml.CRX(0.2, wires=["w1", "w2"])
            qml.CRX(0.3, wires=["w2", "w1"])

        transformed_qfunc = merge_rotations(qfunc)

        ops = qml.transforms.make_tape(transformed_qfunc)().operations

        assert len(ops) == 2

        assert ops[0].name == "CRX"
        assert ops[0].wires == Wires(["w1", "w2"])
        assert ops[0].parameters[0] == 0.2

        assert ops[1].name == "CRX"
        assert ops[1].wires == Wires(["w2", "w1"])
        assert ops[1].parameters[0] == 0.3
