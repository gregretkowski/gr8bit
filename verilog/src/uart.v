// https://learn.lushaylabs.com/tang-nano-9k-debugging/
//`default_nettype none
module uart
#(
    parameter DELAY_FRAMES = 234 // 27,000,000 (27Mhz) / 115200 Baud rate
)
(
    // Connections to FPGA
    input full_clk,
    input uart_rx,
    output uart_tx,
    // Connectons to CPU
    input cpu_clk,
    input [7:0] send_in,
    input set_send, // when memory loc is selected, and ~mo. (indicating cpu write)
    input set_recv_clear, // when memory loc is selected, and mo. (indicating cpu read)
    output [7:0] recv_out,
    output get_recv // is there a byte available that hasnt been read yet?
);

reg [7:0] send_reg = 0;
reg [7:0] recv_reg = 0;
// Says if something is in either register to be sent/gotten.
reg send_av_reg = 0;
reg recv_av_reg = 0;

assign recv_out = recv_reg;
assign get_recv = recv_av_reg;

//reg set_recv_clear = 0;
//reg [7:0] data_in_reg = 0;
//reg set_char_av = 0;


always @(posedge cpu_clk) begin
    if (set_send) begin
        send_reg <= send_in;
        //send_av_reg <= 1;
    end

end


/*
pins as per Digital.
i: data_in 8bit (char to send to uart terminal)
i: clk 1bit
i: send (send a char to the uart terminal)
o: char_av 1bit (there is a char avail to send from uart to cpu)
o: data_out 8bit (send from uart reg to cpu)

If send is set (posedge send):
send char from data_in register,
reset internal send trigger to 0.

if char gotten from terminal.
set char_av to 1
set data_out register
?? How to reset char_av to 0 ??

*/


localparam HALF_DELAY_WAIT = (DELAY_FRAMES / 2);


reg [3:0] rxState = 0;
reg [12:0] rxCounter = 0;
reg [7:0] dataIn = 0;
reg [2:0] rxBitNumber = 0;
reg byteReady = 0;

localparam RX_STATE_IDLE = 0;
localparam RX_STATE_START_BIT = 1;
localparam RX_STATE_READ_WAIT = 2;
localparam RX_STATE_READ = 3;
localparam RX_STATE_STOP_BIT = 5;

// Data coming in from serial port (user terminal) -- AKA RECV
always @(posedge full_clk) begin
    if (set_recv_clear) begin
        recv_av_reg <= 0;
    end
    case (rxState)
        RX_STATE_IDLE: begin
            if (uart_rx == 0) begin
                rxState <= RX_STATE_START_BIT;
                rxCounter <= 1;
                rxBitNumber <= 0;
                recv_av_reg <= 0;
                //byteReady <= 0;
            end
        end
        RX_STATE_START_BIT: begin
            if (rxCounter == HALF_DELAY_WAIT) begin
                rxState <= RX_STATE_READ_WAIT;
                rxCounter <= 1;
            end else
                rxCounter <= rxCounter + 1'b1;
        end
        RX_STATE_READ_WAIT: begin
            rxCounter <= rxCounter + 1'b1;
            if ((rxCounter + 1) == DELAY_FRAMES) begin
                rxState <= RX_STATE_READ;
            end
        end
        RX_STATE_READ: begin
            rxCounter <= 1;
            recv_reg <= {uart_rx, recv_reg[7:1]};
            rxBitNumber <= rxBitNumber + 1'b1;
            if (rxBitNumber == 3'b111)
                rxState <= RX_STATE_STOP_BIT;
            else
                rxState <= RX_STATE_READ_WAIT;
        end
        RX_STATE_STOP_BIT: begin
            rxCounter <= rxCounter + 1'b1;
            if ((rxCounter + 1'b1) == DELAY_FRAMES) begin
                rxState <= RX_STATE_IDLE;
                rxCounter <= 0;
                // byteReady <= 1;
                recv_av_reg <= 1;
            
            end
        end
    endcase
end

/*
always @(posedge clk) begin
    if (byteReady) begin
        led <= ~dataIn[5:0];
    end
end
*/

reg [3:0] txState = 0;
reg [24:0] txCounter = 0;
reg [7:0] dataOut = 0;
reg txPinRegister = 1;
reg [2:0] txBitNumber = 0;
reg [3:0] txByteCounter = 0;

assign uart_tx = txPinRegister;

localparam TX_STATE_IDLE = 0;
localparam TX_STATE_START_BIT = 1;
localparam TX_STATE_WRITE = 2;
localparam TX_STATE_STOP_BIT = 3;
localparam TX_STATE_DEBOUNCE = 4;

// Data going out to serial port (user terminal) - AKA SEND
always @(posedge full_clk) begin
    if (set_send) begin
        send_av_reg <= 1;
    end
    case (txState)
        TX_STATE_IDLE: begin
            //if (btn1 == 0) begin
            if (send_av_reg == 1) begin
                txState <= TX_STATE_START_BIT;
                txCounter <= 0;
                txByteCounter <= 0;
            end
            else begin
                txPinRegister <= 1;
            end
        end
        TX_STATE_START_BIT: begin
            txPinRegister <= 0;
            if ((txCounter + 1'b1) == DELAY_FRAMES) begin
                txState <= TX_STATE_WRITE;
                dataOut <= send_reg; //testMemory[txByteCounter];
                txBitNumber <= 0;
                txCounter <= 0;
            end else
                txCounter <= txCounter + 1'b1;
        end
        TX_STATE_WRITE: begin
            txPinRegister <= dataOut[txBitNumber];
            if ((txCounter +1) == DELAY_FRAMES) begin
                if (txBitNumber == 3'b111) begin
                    txState <= TX_STATE_STOP_BIT;
                end else begin
                    // send bit complete, send next bit
                    txState <= TX_STATE_WRITE;
                    txBitNumber <= txBitNumber + 1'b1;
                end
                txCounter <= 0;
            end else
                txCounter <= txCounter + 1'b1;
        end
        TX_STATE_STOP_BIT: begin
            txPinRegister <= 1;
            if ((txCounter + 1'b1) == DELAY_FRAMES) begin
                // sent whole char, go into idle.
                txState <= TX_STATE_IDLE;
                send_av_reg <= 0;
                txCounter <= 0;
            end else
                txCounter <= txCounter + 1'b1;
        end
        /*
        TX_STATE_DEBOUNCE: begin
            if (txCounter == 23'b111111111111111111) begin
                if (btn1 == 1)
                    txState <= TX_STATE_IDLE;
            end else
                txCounter <= txCounter + 1;
        end */
    endcase
end








endmodule
