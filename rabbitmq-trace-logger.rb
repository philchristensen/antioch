#!/home/mqtester/.rvm/wrappers/ruby-1.9.2-p290@mqtester/ruby
# encoding: utf-8

require "rubygems"
require "amqp"

@exchange_name = "amq.rabbitmq.trace"

class Consumer
  def handle_message(metadata, payload)
     puts "routing_key: #{metadata.routing_key}, payload: #{payload}"
  end
end

class Worker
  def initialize(channel, exchange_name, queue_name, consumer = Consumer.new)
    @exchange_name = exchange_name
    @queue_name = queue_name

    @channel = channel
    @channel.on_error(&method(:handle_channel_exception))

    @consumer = consumer
  end

  def start
    @exchange = @channel.topic(@exchange_name, :durable => true, :auto_delete => false, :internal => true)
    @queue = @channel.queue(@queue_name, :durable => false, :auto_delete => true)
    @queue.bind(@exchange, :routing_key => '#')
    @queue.subscribe(&@consumer.method(:handle_message))
  end

  def handle_channel_exception(channel, channel_close)
    puts "Oops... a channel-level exception: code = #{channel_close.reply_code}, message = #{channel_close.reply_text}"
  end
end

AMQP.start("amqp://guest:guest@localhost") do |connection, open_ok|
  channel = AMQP::Channel.new(connection)
  worker = Worker.new(channel, @exchange_name, '')
  worker.start
end
