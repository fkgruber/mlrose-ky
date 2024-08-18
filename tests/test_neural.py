import pytest
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit, learning_curve
from mlrose_ky.neural.linear_regression import LinearRegression
from mlrose_ky.neural.logistic_regression import LogisticRegression
from mlrose_ky.neural.fitness.network_weights import NetworkWeights
from mlrose_ky.neural.neural_network import NeuralNetwork
from mlrose_ky.opt_probs import ContinuousOpt
from mlrose_ky.neural._nn_base import _NNBase
from mlrose_ky import flatten_weights, unflatten_weights, identity, sigmoid, softmax
from mlrose_ky.algorithms.gd import gradient_descent


@pytest.fixture
def sample_data():
    X = np.array([[0, 1, 0, 1], [0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 1, 1], [0, 0, 1, 1], [1, 0, 0, 0]])
    y_classifier = np.reshape(np.array([1, 1, 0, 0, 1, 1]), [6, 1])
    y_multiclass = np.array([[1, 1], [1, 0], [0, 0], [0, 0], [1, 0], [1, 1]])
    y_regressor = y_classifier.copy()
    return X, y_classifier, y_multiclass, y_regressor


class TestNeural:
    def test_flatten_weights(self):
        x = np.arange(12)
        y = np.arange(6)
        z = np.arange(16)

        a = np.reshape(x, (4, 3))
        b = np.reshape(y, (3, 2))
        c = np.reshape(z, (2, 8))

        weights = [a, b, c]
        flat = list(x) + list(y) + list(z)

        assert np.array_equal(np.array(flatten_weights(weights)), np.array(flat))

    def test_unflatten_weights(self):
        x = np.arange(12)
        y = np.arange(6)
        z = np.arange(16)

        a = np.reshape(x, (4, 3))
        b = np.reshape(y, (3, 2))
        c = np.reshape(z, (2, 8))

        flat = list(x) + list(y) + list(z)
        nodes = [4, 3, 2, 8]
        weights = list(unflatten_weights(np.asarray(flat), nodes))

        assert np.array_equal(weights[0], a) and np.array_equal(weights[1], b) and np.array_equal(weights[2], c)

    def test_gradient_descent(self, sample_data):
        X, y_classifier, _, _ = sample_data
        node_list = [4, 2, 1]
        nodes = 0
        for i in range(len(node_list) - 1):
            nodes += node_list[i] * node_list[i + 1]
        fitness = NetworkWeights(X, y_classifier, node_list, activation=identity, bias=False, is_classifier=False)

        problem = ContinuousOpt(nodes, fitness, maximize=False, min_val=-1)

        test_weights = np.ones(nodes)
        test_fitness = -1 * problem.eval_fitness(test_weights)
        best_state, best_fitness, _ = gradient_descent(problem)

        assert len(best_state) == nodes and min(best_state) >= -1 and max(best_state) <= 1 and best_fitness < test_fitness

    def test_gradient_descent_iter1(self, sample_data):
        X, y_classifier, _, _ = sample_data
        nodes = [4, 2, 1]
        fitness = NetworkWeights(X, y_classifier, nodes, activation=identity, bias=False, is_classifier=False)

        problem = ContinuousOpt(10, fitness, maximize=False, min_val=-1)
        init_weights = np.ones(10)
        best_state, best_fitness, _ = gradient_descent(problem, max_iters=1, init_state=init_weights)
        x = np.array([-0.7, -0.7, -0.9, -0.9, -0.9, -0.9, -1, -1, -1, -1])

        assert np.allclose(best_state, x, atol=0.001) and round(best_fitness, 2) == 19.14


class TestNeuralWeights:
    def test_evaluate_no_bias_classifier(self, sample_data):
        X, y_classifier, _, _ = sample_data
        nodes = [4, 2, 1]
        fitness = NetworkWeights(X, y_classifier, nodes, activation=identity, bias=False)

        a = list(np.arange(8) + 1)
        b = list(0.01 * (np.arange(2) + 1))
        weights = a + b

        assert round(fitness.evaluate(np.asarray(weights)), 4) == 0.7393

    def test_evaluate_no_bias_multi(self, sample_data):
        X, _, y_multiclass, _ = sample_data
        nodes = [4, 2, 2]
        fitness = NetworkWeights(X, y_multiclass, nodes, activation=identity, bias=False)

        a = list(np.arange(8) + 1)
        b = list(0.01 * (np.arange(4) + 1))
        weights = a + b

        assert round(fitness.evaluate(np.asarray(weights)), 4) == 0.7183

    def test_evaluate_no_bias_regressor(self, sample_data):
        X, _, _, y_regressor = sample_data
        nodes = [4, 2, 1]
        fitness = NetworkWeights(X, y_regressor, nodes, activation=identity, bias=False, is_classifier=False)

        a = list(np.arange(8) + 1)
        b = list(0.01 * (np.arange(2) + 1))
        weights = a + b

        assert round(fitness.evaluate(np.asarray(weights)), 4) == 0.5542

    def test_evaluate_bias_regressor(self, sample_data):
        X, _, _, y_regressor = sample_data
        nodes = [5, 2, 1]
        fitness = NetworkWeights(X, y_regressor, nodes, activation=identity, is_classifier=False)

        a = list(np.arange(10) + 1)
        b = list(0.01 * (np.arange(2) + 1))
        weights = a + b

        assert round(fitness.evaluate(np.asarray(weights)), 4) == 0.4363

    def test_calculate_updates(self, sample_data):
        X, y_classifier, _, _ = sample_data
        nodes = [4, 2, 1]
        fitness = NetworkWeights(X, y_classifier, nodes, activation=identity, bias=False, is_classifier=False, learning_rate=1)

        a = list(np.arange(8) + 1)
        b = list(0.01 * (np.arange(2) + 1))
        weights = a + b
        fitness.evaluate(np.asarray(weights))

        updates = list(fitness.calculate_updates())
        update1 = np.array([[-0.0017, -0.0034], [-0.0046, -0.0092], [-0.0052, -0.0104], [0.0014, 0.0028]])
        update2 = np.array([[-3.17], [-4.18]])

        assert np.allclose(updates[0], update1, atol=0.001) and np.allclose(updates[1], update2, atol=0.001)


class TestNeuralNetwork:
    def test_fit_random_hill_climb(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = NeuralNetwork(hidden_nodes=[2], activation="identity", bias=False, learning_rate=1, clip_max=1)

        node_list = [4, 2, 1]
        num_weights = _NNBase._calculate_state_size(node_list)
        weights = np.ones(num_weights)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 10 and len(fitted) == 10 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_simulated_annealing(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = NeuralNetwork(
            hidden_nodes=[2], activation="identity", algorithm="simulated_annealing", bias=False, learning_rate=1, clip_max=1
        )

        node_list = [4, 2, 1]
        num_weights = _NNBase._calculate_state_size(node_list)
        weights = np.ones(num_weights)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 10 and len(fitted) == 10 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_genetic_alg(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = NeuralNetwork(
            hidden_nodes=[2], activation="identity", algorithm="genetic_alg", bias=False, learning_rate=1, clip_max=1, max_attempts=1
        )

        network.fit(X, y_classifier)
        fitted = network.fitted_weights

        assert sum(fitted) < 10 and len(fitted) == 10 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_gradient_descent(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = NeuralNetwork(
            hidden_nodes=[2], activation="identity", algorithm="gradient_descent", bias=False, learning_rate=1, clip_max=1
        )

        node_list = [4, 2, 1]
        num_weights = _NNBase._calculate_state_size(node_list)
        weights = np.ones(num_weights)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 10 and len(fitted) == 10 and min(fitted) >= -1 and max(fitted) <= 1

    def test_predict_no_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = NeuralNetwork(hidden_nodes=[2], activation="identity", bias=False, learning_rate=1, clip_max=1)

        node_list = [4, 2, 2]
        network.fitted_weights = np.array([0.2, 0.5, 0.3, 0.4, 0.4, 0.3, 0.5, 0.2, -1, 1, 1, -1])
        network.node_list = node_list
        network.output_activation = softmax

        probs = np.array([[0.40131, 0.59869], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5], [0.31003, 0.68997], [0.64566, 0.35434]])
        labels = np.array([[0, 1], [1, 0], [1, 0], [1, 0], [0, 1], [1, 0]])

        assert np.array_equal(network.predict(X), labels) and np.allclose(network.predicted_probs, probs, atol=0.0001)

    def test_predict_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = NeuralNetwork(hidden_nodes=[2], activation="identity", learning_rate=1, clip_max=1)

        node_list = [5, 2, 2]
        network.fitted_weights = np.array([0.2, 0.5, 0.3, 0.4, 0.4, 0.3, 0.5, 0.2, 1, -1, -0.1, 0.1, 0.1, -0.1])
        network.node_list = node_list
        network.output_activation = softmax

        probs = np.array(
            [[0.39174, 0.60826], [0.40131, 0.59869], [0.40131, 0.59869], [0.40131, 0.59869], [0.38225, 0.61775], [0.41571, 0.58419]]
        )
        labels = np.array([[0, 1], [0, 1], [0, 1], [0, 1], [0, 1], [0, 1]])

        assert np.array_equal(network.predict(X), labels) and np.allclose(network.predicted_probs, probs, atol=0.0001)

    def test_learning_curve(self):
        """Test scikit-learn learning curve method."""
        network = NeuralNetwork(
            hidden_nodes=[2],
            activation="identity",
            algorithm="simulated_annealing",
            curve=True,
            learning_rate=1,
            clip_max=1,
            max_attempts=100,
        )

        X = np.array(
            [
                [0, 1, 0, 1],
                [0, 0, 1, 0],
                [1, 1, 0, 1],
                [1, 0, 1, 1],
                [0, 0, 1, 1],
                [1, 0, 0, 0],
                [1, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 1],
                [1, 1, 0, 0],
                [0, 1, 1, 1],
                [1, 0, 1, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 1, 0, 0],
                [1, 0, 0, 1],
            ]
        )
        y = np.array([1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0])

        train_sizes = [0.5, 1.0]
        cv = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_sizes, train_scores, test_scores = learning_curve(network, X, y, train_sizes=train_sizes, cv=cv, scoring="accuracy")

        assert not np.isnan(train_scores).any() and not np.isnan(test_scores).any()


class TestLinearRegression:
    def test_fit_random_hill_climb(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LinearRegression(bias=False, learning_rate=1, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_simulated_annealing(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LinearRegression(algorithm="simulated_annealing", bias=False, learning_rate=1, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_genetic_alg(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LinearRegression(algorithm="genetic_alg", bias=False, learning_rate=1, clip_max=1, max_attempts=1)

        network.fit(X, y_classifier)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_gradient_descent(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LinearRegression(algorithm="gradient_descent", bias=False, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) <= 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_predict_no_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = LinearRegression(bias=False, learning_rate=1, clip_max=1)

        network.fitted_weights = np.ones(4)
        network.node_list = [4, 1]
        network.output_activation = identity

        x = np.reshape(np.array([2, 0, 4, 4, 2, 1]), [6, 1])

        assert np.array_equal(network.predict(X), x)

    def test_predict_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = LinearRegression(learning_rate=1, clip_max=1)

        network.fitted_weights = np.ones(5)
        network.node_list = [5, 1]
        network.output_activation = identity

        x = np.reshape(np.array([3, 1, 5, 5, 3, 2]), [6, 1])

        assert np.array_equal(network.predict(X), x)


class TestLogisticRegression:
    def test_fit_random_hill_climb(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LogisticRegression(bias=False, learning_rate=1, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_simulated_annealing(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LogisticRegression(algorithm="simulated_annealing", bias=False, learning_rate=1, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_genetic_alg(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LogisticRegression(algorithm="genetic_alg", bias=False, learning_rate=1, clip_max=1, max_iters=2)

        network.fit(X, y_classifier)
        fitted = network.fitted_weights

        assert sum(fitted) < 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_fit_gradient_descent(self, sample_data):
        X, y_classifier, _, _ = sample_data
        network = LogisticRegression(algorithm="gradient_descent", bias=False, clip_max=1)

        weights = np.ones(4)
        network.fit(X, y_classifier, init_weights=weights)
        fitted = network.fitted_weights

        assert sum(fitted) <= 4 and len(fitted) == 4 and min(fitted) >= -1 and max(fitted) <= 1

    def test_predict_no_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = LogisticRegression(bias=False, learning_rate=1, clip_max=1)

        node_list = [4, 1]
        network.fitted_weights = np.array([-1, 1, 1, 1])
        network.node_list = node_list
        network.output_activation = sigmoid

        probs = np.reshape(np.array([0.88080, 0.5, 0.88080, 0.88080, 0.88080, 0.26894]), [6, 1])
        labels = np.reshape(np.array([1, 0, 1, 1, 1, 0]), [6, 1])

        assert np.array_equal(network.predict(X), labels) and np.allclose(network.predicted_probs, probs, atol=0.0001)

    def test_predict_bias(self, sample_data):
        X, _, _, _ = sample_data
        network = LogisticRegression(learning_rate=1, clip_max=1)

        node_list = [5, 1]
        network.fitted_weights = np.array([-1, 1, 1, 1, -1])
        network.node_list = node_list
        network.output_activation = sigmoid

        probs = np.reshape(np.array([0.73106, 0.26894, 0.73106, 0.73106, 0.73106, 0.11920]), [6, 1])
        labels = np.reshape(np.array([1, 0, 1, 1, 1, 0]), [6, 1])

        assert np.array_equal(network.predict(X), labels) and np.allclose(network.predicted_probs, probs, atol=0.0001)
