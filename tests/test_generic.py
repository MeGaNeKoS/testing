import logging
from unittest import TestCase

import pytest

import devlog
from devlog.decorator import LoggingDecorator


def generic_func(arg1, arg2, kwarg1=None, kwarg2=None):
    return arg1 + arg2


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs.

    Messages are available from an instance's ``messages`` dict, in order, indexed by
    a lowercase log level string (e.g., 'debug', 'info', etc.).
    """

    def __init__(self, *args, **kwargs):
        self.messages = {'debug': [], 'info': [], 'warning': [], 'error': [], 'critical': []}
        super().__init__(*args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())
        try:
            self.messages[record.levelname.lower()].append(record.getMessage())
        except Exception:
            self.handleError(record)

    def reset(self):
        self.acquire()
        try:
            for message_list in self.messages.values():
                message_list.clear()
        finally:
            self.release()


class TestDecorators(TestCase):
    def setUp(self):
        self.logger = logging.Logger("mocked")
        self.log_handler = MockLoggingHandler()
        self.logger.addHandler(self.log_handler)

    def test_log_on_start(self):
        wrapped_function = devlog.log_on_start(args_kwargs=False,
                                               logger=self.logger,
                                               message="Start func generic_func with "
                                                       "arg1 = {arg1}, arg2 = {arg2}, "
                                                       "kwarg1 = {kwarg1}, kwarg2 = {kwarg2}"
                                               )(generic_func)
        wrapped_function(1, 2)
        self.assertIn("Start func generic_func with arg1 = 1, arg2 = 2, kwarg1 = None, kwarg2 = None",
                      self.log_handler.messages["info"])

    def test_log_on_start_wo_parentheses(self):
        # has to pass the logger as a kwarg to redirect the output to our mocking handler
        wrapped_function_wo_parentheses = devlog.log_on_start(generic_func, logger=self.logger)
        wrapped_function_wo_parentheses(3, 4)
        self.assertIn("Start func generic_func with args (3, 4), kwargs {}", self.log_handler.messages["info"])

    def test_log_on_start_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_start(logger=self.logger)(generic_func)
        wrapped_function_parentheses(5, 6)
        self.assertIn("Start func generic_func with args (5, 6), kwargs {}", self.log_handler.messages["info"])

    def test_log_on_start_w_trace_stack(self):
        wrapped_function = devlog.log_on_start(logger=self.logger,
                                               trace_stack=True)(generic_func)
        wrapped_function(1, 2)
        # guarantee that the trace is existed, otherwise the test will fail
        self.assertIn(self.log_handler.messages["debug"][0],
                      self.log_handler.messages["debug"])

    def test_log_on_end(self):
        wrapped_function = devlog.log_on_end(
            args_kwargs=False,
            logger=self.logger,
            message="Successfully run func generic_func with "
                    "arg1 = {arg1}, arg2 = {arg2}, "
                    "kwarg1 = {kwarg1}, kwarg2 = {kwarg2}"
        )(generic_func)
        wrapped_function(1, 2)
        self.assertIn("Successfully run func generic_func with arg1 = 1, arg2 = 2, kwarg1 = None, kwarg2 = None",
                      self.log_handler.messages["info"])

    def test_log_on_end_wo_parentheses(self):
        # has to pass the logger as a kwarg to redirect the output to our mocking handler
        wrapped_function_wo_parentheses = devlog.log_on_end(generic_func, logger=self.logger)
        wrapped_function_wo_parentheses(1, 2)
        self.assertIn("Successfully run func generic_func with args (1, 2), kwargs {}",
                      self.log_handler.messages["info"])

    def test_log_on_end_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_end(logger=self.logger)(generic_func)
        wrapped_function_parentheses(1, 2)
        self.assertIn("Successfully run func generic_func with args (1, 2), kwargs {}",
                      self.log_handler.messages["info"])

    def test_log_on_end_w_trace_stack(self):
        wrapped_function = devlog.log_on_end(logger=self.logger,
                                             trace_stack=True)(generic_func)
        wrapped_function(1, 2)
        self.assertIn(self.log_handler.messages["debug"][0],
                      self.log_handler.messages["debug"])

    def test_log_on_error(self):
        wrapped_function = devlog.log_on_error(logger=self.logger, trace_stack=True)(generic_func)
        with pytest.raises(TypeError):
            wrapped_function(1, "abc")

            self.assertIn('End of the trace test_generic:test_func',
                          self.log_handler.messages["debug"])

    def test_log_on_error_wo_parentheses(self):
        wrapped_function_wo_parentheses = devlog.log_on_error(generic_func, logger=self.logger)
        with pytest.raises(TypeError):
            wrapped_function_wo_parentheses(2, "abc")

            self.assertIn(
                'Error in func test_func with args (2, \'abc\'), kwargs {}',
                self.log_handler.messages["error"])

    def test_log_on_error_w_parentheses(self):
        wrapped_function_parentheses = devlog.log_on_error(logger=self.logger)(generic_func)
        with pytest.raises(TypeError):
            wrapped_function_parentheses(3, "abc")

            self.assertIn(
                'Error in func test_func with args (3, \'abc\'), kwargs {}',
                self.log_handler.messages["error"])

    def test_log_on_error_w_trace_stack(self):
        with pytest.raises(TypeError):
            wrapped_function = devlog.log_on_error(logger=self.logger,
                                                   trace_stack=True)(generic_func)
            wrapped_function(4, "abc")
            self.assertIn('End of the trace test_generic:generic_func',
                          self.log_handler.messages["debug"])

    def test_logger_handler(self):
        decorator = LoggingDecorator(logging.INFO, "", logger=self.logger, handler=self.log_handler)
        self.assertEqual(decorator.get_logger(generic_func).name, self.logger.name)

    def test_handler(self):
        decorator = LoggingDecorator(logging.INFO, "", handler=self.log_handler)
        self.assertEqual(decorator.get_logger(generic_func).name, "test_generic")
